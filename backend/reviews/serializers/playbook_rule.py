from rest_framework import serializers

from reviews.models import PlaybookRule


class PlaybookRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlaybookRule
        fields = [
            "key",
            "name",
            "category",
            "default_risk",
            "missing_risk",
            "missing_reason",
            "active",
            "order",
        ]
