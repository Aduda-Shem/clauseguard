from django.db import models

from reviews.models.review_result import ReviewResult


class ClauseFinding(models.Model):
    review_result = models.ForeignKey(ReviewResult, related_name="findings", on_delete=models.CASCADE)
    rule_key = models.SlugField()
    category = models.CharField(max_length=100)
    risk_level = models.CharField(max_length=20)
    is_missing = models.BooleanField(default=False)
    matched_text = models.TextField(blank=True)
    reason = models.TextField()
    redline_suggestion = models.TextField(blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.category} [{self.risk_level}]"
