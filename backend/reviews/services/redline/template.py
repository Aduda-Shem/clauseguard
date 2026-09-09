from reviews.services.redline.base import RedlineBatchResult, RedlineClient, RedlineRequest


class TemplateRedlineClient(RedlineClient):
    """Offline, zero-cost -- returns the playbook's canned text unchanged."""

    def draft(self, requests: list[RedlineRequest], findings_summary: str) -> RedlineBatchResult:
        return RedlineBatchResult(
            redlines={r.rule_key: r.fallback for r in requests},
            summary=findings_summary,
        )
