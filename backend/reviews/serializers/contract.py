from rest_framework import serializers

from reviews.models import Contract
from reviews.serializers.review_result import ReviewResultSerializer


class ContractSerializer(serializers.ModelSerializer):
    review_result = ReviewResultSerializer(read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "filename",
            "status",
            "error_message",
            "uploaded_at",
            "review_result",
        ]


class ContractListSerializer(serializers.ModelSerializer):
    overall_risk = serializers.CharField(source="review_result.overall_risk", default=None, read_only=True)
    next_action = serializers.CharField(source="review_result.next_action", default=None, read_only=True)

    class Meta:
        model = Contract
        fields = ["id", "filename", "status", "uploaded_at", "overall_risk", "next_action"]
