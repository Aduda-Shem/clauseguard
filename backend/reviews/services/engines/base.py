from abc import ABC, abstractmethod
from dataclasses import dataclass

RISK_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


@dataclass
class Finding:
    rule_key: str
    category: str
    risk_level: str
    is_missing: bool
    matched_text: str
    reason: str
    redline_suggestion: str


class RiskAnalysisEngine(ABC):
    @abstractmethod
    def analyze(self, text: str, rules) -> list[Finding]:
        raise NotImplementedError


def overall_risk(findings: list[Finding]) -> str:
    if not findings:
        return "Low"
    return max((f.risk_level for f in findings), key=lambda r: RISK_ORDER.get(r, 0))


def next_action_for(findings: list[Finding]) -> str:
    return {
        "Critical": "ESCALATE",
        "High": "NEGOTIATE",
        "Medium": "APPROVE_WITH_CONDITIONS",
    }.get(overall_risk(findings), "APPROVE")
