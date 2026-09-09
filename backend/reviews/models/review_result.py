from django.db import models

from reviews.models.contract import Contract


class ReviewResult(models.Model):
    class NextAction(models.TextChoices):
        APPROVE = "APPROVE", "Approve"
        APPROVE_WITH_CONDITIONS = "APPROVE_WITH_CONDITIONS", "Approve with conditions"
        NEGOTIATE = "NEGOTIATE", "Negotiate"
        ESCALATE = "ESCALATE", "Escalate to legal"

    class EngineMode(models.TextChoices):
        RULE_BASED = "RULE_BASED", "Rule-based only"
        LLM_ENHANCED = "LLM_ENHANCED", "Rule-based + LLM redlines"

    contract = models.OneToOneField(Contract, related_name="review_result", on_delete=models.CASCADE)
    overall_risk = models.CharField(max_length=20)
    next_action = models.CharField(max_length=30, choices=NextAction.choices)
    summary = models.TextField()
    engine_mode = models.CharField(max_length=20, choices=EngineMode.choices)
    processing_time_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review of {self.contract} -> {self.next_action}"
