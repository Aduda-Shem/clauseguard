from rest_framework import serializers

from reviews.models import ClauseFinding


class ClauseFindingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClauseFinding
        fields = [
            "id",
            "rule_key",
            "category",
            "risk_level",
            "is_missing",
            "matched_text",
            "reason",
            "redline_suggestion",
        ]
