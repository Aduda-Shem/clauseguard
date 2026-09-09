from rest_framework import serializers

from reviews.models import ReviewResult
from reviews.serializers.clause_finding import ClauseFindingSerializer


class ReviewResultSerializer(serializers.ModelSerializer):
    findings = ClauseFindingSerializer(many=True, read_only=True)

    class Meta:
        model = ReviewResult
        fields = [
            "id",
            "overall_risk",
            "next_action",
            "summary",
            "engine_mode",
            "processing_time_ms",
            "created_at",
            "findings",
        ]
