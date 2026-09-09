from django.db import models


class PlaybookRule(models.Model):
    key = models.SlugField(unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    detection_pattern = models.TextField(
        help_text="Regex (case-insensitive) used to locate this clause's paragraph in the contract text."
    )
    risk_rules = models.JSONField(
        default=list,
        help_text=(
            "Ordered list of {pattern, risk, reason, redline}. First regex that matches "
            "inside the detected clause wins; evaluated top to bottom."
        ),
    )
    default_risk = models.CharField(max_length=20, default="Low")
    default_reason = models.TextField(
        blank=True,
        help_text="Reason used when the clause is detected but no specific risk_rules pattern matches.",
    )
    default_redline = models.TextField(blank=True)
    missing_risk = models.CharField(
        max_length=20,
        default="Low",
        help_text="Risk level to report when this clause category is not found in the contract at all.",
    )
    missing_reason = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "key"]

    def __str__(self):
        return self.name
