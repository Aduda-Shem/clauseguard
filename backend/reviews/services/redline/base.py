from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RedlineRequest:
    """One Medium+ finding that needs a redline suggestion."""

    rule_key: str
    category: str
    matched_text: str
    reason: str
    fallback: str


@dataclass
class RedlineBatchResult:
    redlines: dict[str, str]  # rule_key -> redline text
    summary: str


class RedlineClient(ABC):
    @abstractmethod
    def draft(self, requests: list[RedlineRequest], findings_summary: str) -> RedlineBatchResult:
        """One call for the whole review, not one per finding -- a contract
        with N flagged findings previously made N+1 LLM calls (one redline
        each, plus a summary), which trivially exceeds a 5-requests/minute
        free-tier quota on its own. See docs/EVALUATION.md."""
        raise NotImplementedError
