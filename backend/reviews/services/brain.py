import time

from django.db import transaction

from reviews.models import ChatMessage, ClauseFinding, Contract, ReviewResult
from reviews.repositories import PlaybookRepository
from reviews.services.chat.base import ChatClient
from reviews.services.chat.factory import get_chat_client
from reviews.services.engines.base import (
    RISK_ORDER,
    Finding,
    RiskAnalysisEngine,
    next_action_for,
    overall_risk,
)
from reviews.services.engines.regex_engine import RegexRiskAnalysisEngine
from reviews.services.llm_config import is_llm_configured
from reviews.services.redline.base import RedlineClient, RedlineRequest
from reviews.services.redline.factory import get_redline_client

REDLINE_RISK_THRESHOLD = {"Medium", "High", "Critical"}
MAX_CHAT_HISTORY_TURNS = 6


def _build_summary(findings: list[Finding]) -> str:
    by_risk: dict[str, list[Finding]] = {}
    for f in findings:
        by_risk.setdefault(f.risk_level, []).append(f)

    parts = [
        f"{len(by_risk[level])} {level}-risk item(s): {', '.join(f.category for f in by_risk[level])}"
        for level in ("Critical", "High", "Medium")
        if by_risk.get(level)
    ]
    if not parts:
        return "No Medium, High, or Critical risk clauses were found against the current playbook."
    return "; ".join(parts) + "."


def _findings_context(contract: Contract) -> str:
    """Worst risk first, so a fallback client with no real reasoning ability
    can still answer "what's the biggest risk" correctly by just reading the
    first line -- see TemplateChatClient.answer()."""
    result = getattr(contract, "review_result", None)
    if not result:
        return "No review has been completed yet."
    findings = sorted(
        (f for f in result.findings.all() if not f.is_missing),
        key=lambda f: RISK_ORDER.get(f.risk_level, -1),
        reverse=True,
    )
    lines = [f"- {f.category} [{f.risk_level}]: {f.reason}" for f in findings]
    return "\n".join(lines) or "No risk findings against the current playbook."


class ContractBrain:
    """Single entry point for everything AI does with one contract:
    running its risk review and answering chat questions about it.
    Mirrors this codebase's sibling Aila project's `BrandBrainService` --
    one object per entity, lazily-loaded sub-services, multiple capability
    methods (`review()`, `ask()`) instead of a scattered function per
    concern. The API views, the eval harness, and management commands all
    go through this."""

    def __init__(
        self,
        contract: Contract,
        engine: RiskAnalysisEngine = None,
        redline_client: RedlineClient = None,
        chat_client: ChatClient = None,
    ):
        self.contract = contract
        self._engine = engine
        self._redline_client = redline_client
        self._chat_client = chat_client

    @property
    def engine(self) -> RiskAnalysisEngine:
        if self._engine is None:
            self._engine = RegexRiskAnalysisEngine()
        return self._engine

    @property
    def redline_client(self) -> RedlineClient:
        if self._redline_client is None:
            self._redline_client = get_redline_client()
        return self._redline_client

    @property
    def chat_client(self) -> ChatClient:
        if self._chat_client is None:
            self._chat_client = get_chat_client()
        return self._chat_client

    @transaction.atomic
    def review(self) -> ReviewResult:
        started = time.monotonic()
        self.contract.status = Contract.Status.PROCESSING
        self.contract.save(update_fields=["status"])

        rules = PlaybookRepository.get_active_rules()
        findings = self.engine.analyze(self.contract.source_text, rules)

        redline_requests = [
            RedlineRequest(
                rule_key=f.rule_key,
                category=f.category,
                matched_text=f.matched_text,
                reason=f.reason,
                fallback=f.redline_suggestion,
            )
            for f in findings
            if not f.is_missing and f.risk_level in REDLINE_RISK_THRESHOLD
        ]
        batch_result = self.redline_client.draft(redline_requests, _build_summary(findings))
        redlines_by_key = batch_result.redlines
        for f in findings:
            if f.rule_key in redlines_by_key:
                f.redline_suggestion = redlines_by_key[f.rule_key]

        summary = batch_result.summary
        engine_mode = (
            ReviewResult.EngineMode.LLM_ENHANCED if is_llm_configured() else ReviewResult.EngineMode.RULE_BASED
        )
        elapsed_ms = int((time.monotonic() - started) * 1000)

        ReviewResult.objects.filter(contract=self.contract).delete()
        result = ReviewResult.objects.create(
            contract=self.contract,
            overall_risk=overall_risk(findings),
            next_action=next_action_for(findings),
            summary=summary,
            engine_mode=engine_mode,
            processing_time_ms=elapsed_ms,
        )
        ClauseFinding.objects.bulk_create(
            ClauseFinding(
                review_result=result,
                rule_key=f.rule_key,
                category=f.category,
                risk_level=f.risk_level,
                is_missing=f.is_missing,
                matched_text=f.matched_text,
                reason=f.reason,
                redline_suggestion=f.redline_suggestion,
            )
            for f in findings
        )

        self.contract.status = Contract.Status.COMPLETE
        self.contract.save(update_fields=["status"])
        return result

    def ask(self, question: str) -> tuple[ChatMessage, ChatMessage]:
        user_message = ChatMessage.objects.create(
            contract=self.contract, role=ChatMessage.Role.USER, content=question
        )

        history = list(
            ChatMessage.objects.filter(contract=self.contract)
            .exclude(id=user_message.id)
            .order_by("-created_at")[:MAX_CHAT_HISTORY_TURNS]
        )
        history.reverse()
        history_payload = [{"role": m.role, "content": m.content} for m in history]

        answer_text = self.chat_client.answer(
            question=question,
            contract_text=self.contract.source_text,
            findings_context=_findings_context(self.contract),
            history=history_payload,
        )

        assistant_message = ChatMessage.objects.create(
            contract=self.contract, role=ChatMessage.Role.ASSISTANT, content=answer_text
        )
        return user_message, assistant_message
