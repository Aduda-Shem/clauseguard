import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from reviews.models import PlaybookRule


@pytest.fixture
def user(db):
    return User.objects.create_user(username="alice", password="testpass123")


@pytest.fixture(autouse=True)
def playbook(db):
    PlaybookRule.objects.create(
        key="liability-cap",
        name="Limitation of liability",
        category="Liability",
        detection_pattern=r"liab",
        risk_rules=[{"pattern": "unlimited", "risk": "Critical", "reason": "uncapped exposure", "redline": "cap it"}],
        default_risk="Medium",
        default_reason="present",
        default_redline="",
        missing_risk="High",
        missing_reason="no cap found",
        order=1,
    )


@pytest.fixture
def client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client
