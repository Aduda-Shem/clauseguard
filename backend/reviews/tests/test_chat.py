import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from reviews.models import PlaybookRule
from reviews.services.chat.template import TemplateChatClient


def test_template_chat_client_finds_relevant_paragraph():
    client = TemplateChatClient()
    text = "Payment terms are net 90 from invoice date.\n\nGoverning law is Delaware."
    answer = client.answer("what are the payment terms?", text, "", [])
    assert "net 90" in answer


def test_template_chat_client_no_match_found():
    client = TemplateChatClient()
    answer = client.answer("what color is the sky?", "This is a contract about widgets.", "", [])
    assert "couldn't find" in answer.lower()


def test_template_chat_client_empty_question():
    client = TemplateChatClient()
    answer = client.answer("   ", "some contract text", "", [])
    assert "ask a specific question" in answer.lower()


def test_template_chat_client_prefers_rare_word_over_common_one():
    """A word repeated across many segments (e.g. 'agreement' in every
    heading) should carry less weight than a rare, distinguishing word --
    otherwise the match degenerates into 'first segment sharing any common
    word', which is exactly the kind of irrelevant match this was built to
    avoid."""
    client = TemplateChatClient()
    text = (
        "This Agreement governs the relationship.\n\n"
        "Any dispute shall be resolved through binding arbitration in New York.\n\n"
        "This Agreement may be amended in writing."
    )
    answer = client.answer("What happens if there is a dispute under the agreement?", text, "", [])
    assert "arbitration" in answer.lower()


def test_template_chat_client_avoids_short_fragment_when_fuller_match_exists():
    client = TemplateChatClient()
    text = (
        "Notice.\n\n"
        "Either party may terminate this agreement upon thirty (30) days written "
        "notice to the other party."
    )
    answer = client.answer("how do I give notice to terminate?", text, "", [])
    assert "30" in answer


def test_template_chat_client_answers_risk_question_from_findings():
    """'What's the biggest risk' can't be answered by keyword-searching the
    contract text for the literal word "risk" (real contracts don't
    describe themselves that way) -- it should be answered from the
    already-computed, worst-first findings instead."""
    client = TemplateChatClient()
    findings_context = (
        "- Liability [Critical]: Liability is explicitly uncapped or unlimited.\n"
        "- Payment [High]: Extended payment terms of 90+ days strain cash flow."
    )
    answer = client.answer(
        "What's the biggest risk in this contract?",
        "This is a long contract with many clauses about various topics.",
        findings_context,
        [],
    )
    assert "Liability" in answer
    assert "Critical" in answer
    assert "uncapped" in answer


def test_template_chat_client_falls_back_to_text_search_when_no_findings():
    """A risk-intent question with nothing to answer from (no review yet, or
    a clean contract with zero findings) should fall through to the normal
    keyword search rather than returning a confusing empty risk answer."""
    client = TemplateChatClient()
    text = "This Agreement covers the sale of widgets and includes risk of loss provisions for shipping."
    answer = client.answer("what's the risk here?", text, "No review has been completed yet.", [])
    assert "risk of loss" in answer.lower()


@pytest.mark.django_db
def test_chat_answers_biggest_risk_question_from_real_findings(client):
    # Two findings of different severity -- this is what actually catches an
    # ordering bug; a single-finding contract can't (the "top concern" pick
    # was silently wrong -- lowest risk first -- until caught by hand).
    PlaybookRule.objects.create(
        key="auto-renewal",
        name="Auto-renewal",
        category="Auto-renewal",
        detection_pattern=r"renew",
        risk_rules=[],
        default_risk="Medium",
        default_reason="present",
        default_redline="",
        missing_risk="Low",
        missing_reason="no renewal clause",
        order=2,
    )
    create_resp = client.post(
        "/api/contracts/",
        {
            "filename": "t.txt",
            "text": "This agreement shall automatically renew. Separately, liability shall be unlimited.",
        },
        format="json",
    )
    contract_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/contracts/{contract_id}/chat/", {"question": "What's the biggest risk in this contract?"}, format="json"
    )
    assert resp.status_code == 201
    answer = resp.json()["assistant_message"]["content"]
    assert "top concern is: Liability [Critical]" in answer
    assert "Auto-renewal [Medium]" in answer  # present, but correctly not the top pick


@pytest.mark.django_db
def test_chat_requires_completed_review(client):
    create_resp = client.post(
        "/api/contracts/", {"filename": "t.txt", "text": "liability shall be unlimited"}, format="json"
    )
    contract_id = create_resp.json()["id"]

    # Simulate a not-yet-complete contract by asking on one that failed/pending -- easiest
    # repeatable way here is to point at a contract id that exists but force status via ORM.
    from reviews.models import Contract

    Contract.objects.filter(id=contract_id).update(status=Contract.Status.PROCESSING)

    resp = client.post(f"/api/contracts/{contract_id}/chat/", {"question": "hi"}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_chat_rejects_empty_question(client):
    create_resp = client.post(
        "/api/contracts/", {"filename": "t.txt", "text": "liability shall be unlimited"}, format="json"
    )
    contract_id = create_resp.json()["id"]
    resp = client.post(f"/api/contracts/{contract_id}/chat/", {"question": "  "}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_chat_creates_and_lists_messages(client):
    create_resp = client.post(
        "/api/contracts/",
        {"filename": "t.txt", "text": "Payment terms are net 90 from invoice date."},
        format="json",
    )
    contract_id = create_resp.json()["id"]

    resp = client.post(f"/api/contracts/{contract_id}/chat/", {"question": "what are the payment terms?"}, format="json")
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_message"]["role"] == "USER"
    assert body["assistant_message"]["role"] == "ASSISTANT"
    assert "net 90" in body["assistant_message"]["content"]

    history_resp = client.get(f"/api/contracts/{contract_id}/chat/")
    assert history_resp.status_code == 200
    assert len(history_resp.json()) == 2


@pytest.mark.django_db
def test_chat_isolated_per_owner(client, user):
    create_resp = client.post(
        "/api/contracts/", {"filename": "t.txt", "text": "liability shall be unlimited"}, format="json"
    )
    contract_id = create_resp.json()["id"]

    other = User.objects.create_user(username="bob", password="testpass123")
    other_client = APIClient()
    other_client.force_authenticate(user=other)

    resp = other_client.post(f"/api/contracts/{contract_id}/chat/", {"question": "hi"}, format="json")
    assert resp.status_code == 404
