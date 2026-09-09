import logging

from pydantic import BaseModel

from reviews.services.redline.base import RedlineBatchResult, RedlineClient, RedlineRequest

logger = logging.getLogger(__name__)


class _RedlineItem(BaseModel):
    rule_key: str
    redline: str


class _RedlineSchema(BaseModel):
    # A dict[str, str] here looks more natural but Gemini's structured
    # output rejects it outright ("additionalProperties is not supported
    # in the Gemini API") -- found by hand, not by any test, since the
    # exception was previously swallowed silently. A list of well-defined
    # objects is the supported shape for a variable-length mapping.
    redlines: list[_RedlineItem]
    summary: str


class GeminiRedlineClient(RedlineClient):
    def __init__(self, api_key: str, model: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def draft(self, requests: list[RedlineRequest], findings_summary: str) -> RedlineBatchResult:
        fallback_result = RedlineBatchResult(
            redlines={r.rule_key: r.fallback for r in requests}, summary=findings_summary
        )
        if not requests:
            # Nothing flagged Medium+ -- a plain-text summary is enough,
            # and skipping the call entirely saves quota for reviews that
            # actually need it.
            return fallback_result

        clauses_block = "\n".join(
            f'- rule_key "{r.rule_key}" ({r.category}): {r.reason} '
            f'Excerpt: "{r.matched_text[:400]}"'
            for r in requests
        )
        prompt = (
            "You are a contract reviewer. For each clause below, write a 1-2 sentence specific, "
            "actionable negotiation note -- concrete enough to paste into an email to the other "
            "party. Then write one 2-3 sentence plain-prose summary of the overall review for a "
            "non-lawyer operations manager deciding whether to sign. No markdown, no preamble, "
            "plain prose only.\n\n"
            f"CLAUSES NEEDING REDLINES:\n{clauses_block}\n\n"
            f"OVERALL FINDINGS:\n{findings_summary}\n\n"
            "Return the redlines keyed by the exact rule_key values shown above."
        )
        try:
            from google.genai import types

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=900,
                    temperature=0.2,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    response_mime_type="application/json",
                    response_schema=_RedlineSchema,
                ),
            )
            parsed: _RedlineSchema = response.parsed
            if not parsed:
                logger.warning("Gemini redline call returned no parsed JSON -- falling back to templates")
                return fallback_result

            redlines_by_key = {item.rule_key: item.redline for item in parsed.redlines}
            redlines = {r.rule_key: redlines_by_key.get(r.rule_key) or r.fallback for r in requests}
            return RedlineBatchResult(redlines=redlines, summary=parsed.summary or findings_summary)
        except Exception:
            logger.warning("Gemini redline call failed -- falling back to templates", exc_info=True)
            return fallback_result
