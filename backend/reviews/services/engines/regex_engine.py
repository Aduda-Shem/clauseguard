import re

from reviews.services.engines.base import RISK_ORDER, Finding, RiskAnalysisEngine

CONTEXT_RADIUS = 220
MAX_OCCURRENCES_PER_RULE = 8


def _context_window(text: str, match: re.Match, radius: int = CONTEXT_RADIUS) -> str:
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return text[start:end].strip()


def _evaluate_window(rule, window: str) -> tuple[str, str, str]:
    risk_level = rule.default_risk
    reason = rule.default_reason or (
        f"A '{rule.name}' clause was found but did not match a specific known risk "
        f"pattern -- review the excerpt manually."
    )
    redline = rule.default_redline

    for risk_rule in rule.risk_rules:
        pattern = risk_rule.get("pattern")
        if not pattern:
            continue
        try:
            hit = re.search(pattern, window, re.IGNORECASE)
        except re.error:
            hit = None
        if not hit:
            continue

        exclude_pattern = risk_rule.get("exclude_pattern")
        if exclude_pattern:
            try:
                excluded = re.search(exclude_pattern, window, re.IGNORECASE)
            except re.error:
                excluded = None
            if excluded:
                continue

        risk_level = risk_rule.get("risk", risk_level)
        reason = risk_rule.get("reason", reason)
        redline = risk_rule.get("redline", redline)
        break

    return risk_level, reason, redline


class RegexRiskAnalysisEngine(RiskAnalysisEngine):
    """Locates each playbook rule's clause via regex and scores it against
    that rule's risk_rules. Every occurrence is evaluated, not just the
    first, and the highest-risk one wins (see docs/EVALUATION.md failure
    case #4 for why first-match-only was wrong)."""

    def analyze(self, text: str, rules) -> list[Finding]:
        findings: list[Finding] = []

        for rule in rules:
            try:
                matches = list(re.finditer(rule.detection_pattern, text, re.IGNORECASE))
            except re.error:
                matches = []

            if not matches:
                findings.append(
                    Finding(
                        rule_key=rule.key,
                        category=rule.category,
                        risk_level=rule.missing_risk,
                        is_missing=True,
                        matched_text="",
                        reason=rule.missing_reason
                        or f"No '{rule.name}' clause was found anywhere in this contract.",
                        redline_suggestion="",
                    )
                )
                continue

            best = None
            for match in matches[:MAX_OCCURRENCES_PER_RULE]:
                window = _context_window(text, match)
                risk_level, reason, redline = _evaluate_window(rule, window)
                if best is None or RISK_ORDER.get(risk_level, 0) > RISK_ORDER.get(best[0], 0):
                    best = (risk_level, reason, redline, window)

            findings.append(
                Finding(
                    rule_key=rule.key,
                    category=rule.category,
                    risk_level=best[0],
                    is_missing=False,
                    matched_text=best[3],
                    reason=best[1],
                    redline_suggestion=best[2],
                )
            )

        return findings
