from types import SimpleNamespace

from reviews.services.engines.base import next_action_for, overall_risk
from reviews.services.engines.regex_engine import RegexRiskAnalysisEngine

engine = RegexRiskAnalysisEngine()


def rule(**kwargs):
    defaults = dict(
        key="test-rule",
        category="Test",
        name="Test Rule",
        detection_pattern=r"widget",
        risk_rules=[],
        default_risk="Low",
        default_reason="",
        default_redline="",
        missing_risk="Low",
        missing_reason="missing",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_missing_clause_reports_missing_risk():
    findings = engine.analyze("no relevant terms here", [rule(missing_risk="High")])
    assert findings[0].is_missing is True
    assert findings[0].risk_level == "High"


def test_detected_clause_uses_default_when_no_risk_rule_matches():
    findings = engine.analyze("the widget is great", [rule(default_risk="Medium")])
    assert findings[0].is_missing is False
    assert findings[0].risk_level == "Medium"


def test_first_matching_risk_rule_wins():
    r = rule(
        detection_pattern=r"liab",
        risk_rules=[
            {"pattern": "unlimited", "risk": "Critical", "reason": "uncapped"},
            {"pattern": "liab", "risk": "Medium", "reason": "generic"},
        ],
    )
    findings = engine.analyze("liability shall be unlimited under this deal", [r])
    assert findings[0].risk_level == "Critical"
    assert findings[0].reason == "uncapped"


def test_risk_rules_evaluated_in_order_first_match_wins_not_best_match():
    r = rule(
        detection_pattern=r"liab",
        risk_rules=[
            {"pattern": "liab", "risk": "Medium", "reason": "generic"},
            {"pattern": "unlimited", "risk": "Critical", "reason": "uncapped"},
        ],
    )
    findings = engine.analyze("liability shall be unlimited under this deal", [r])
    assert findings[0].risk_level == "Medium"


def test_overall_risk_is_max_across_findings():
    findings = engine.analyze(
        "widget alpha, widget beta unlimited",
        [
            rule(key="a", default_risk="Low"),
            rule(key="b", risk_rules=[{"pattern": "unlimited", "risk": "Critical", "reason": "x"}]),
        ],
    )
    assert overall_risk(findings) == "Critical"


def test_next_action_mapping():
    assert next_action_for([SimpleNamespace(risk_level="Critical")]) == "ESCALATE"
    assert next_action_for([SimpleNamespace(risk_level="High")]) == "NEGOTIATE"
    assert next_action_for([SimpleNamespace(risk_level="Medium")]) == "APPROVE_WITH_CONDITIONS"
    assert next_action_for([SimpleNamespace(risk_level="Low")]) == "APPROVE"
    assert next_action_for([]) == "APPROVE"


def test_exclude_pattern_prevents_false_positive_on_standard_carveout():
    r = rule(
        detection_pattern=r"liab",
        risk_rules=[
            {
                "pattern": "shall not be limited",
                "exclude_pattern": "except for",
                "risk": "Critical",
                "reason": "uncapped",
            },
            {"pattern": "exceed.{0,20}fees paid", "risk": "Low", "reason": "standard cap"},
        ],
    )
    findings = engine.analyze(
        "except for fraud, liability shall not be limited; otherwise liability shall not "
        "exceed the fees paid",
        [r],
    )
    assert findings[0].risk_level == "Low"
    assert findings[0].reason == "standard cap"


def test_exclude_pattern_absent_still_triggers_risk():
    r = rule(
        detection_pattern=r"liab",
        risk_rules=[{"pattern": "shall not be limited", "exclude_pattern": "except for", "risk": "Critical", "reason": "uncapped"}],
    )
    findings = engine.analyze("liability shall not be limited under any circumstances", [r])
    assert findings[0].risk_level == "Critical"


def test_malformed_regex_in_risk_rule_does_not_crash():
    r = rule(detection_pattern=r"widget", risk_rules=[{"pattern": "(unclosed", "risk": "High", "reason": "x"}])
    findings = engine.analyze("the widget is here", [r])
    assert findings[0].risk_level == r.default_risk
