import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from reviews.models import Contract


@pytest.mark.django_db
def test_health(client):
    resp = client.get("/api/health/")
    assert resp.status_code == 200


@pytest.mark.django_db
def test_playbook_list(client):
    resp = client.get("/api/playbook/")
    assert resp.status_code == 200
    assert resp.json()[0]["key"] == "liability-cap"


@pytest.mark.django_db
def test_create_contract_from_pasted_text_runs_review(client):
    resp = client.post(
        "/api/contracts/",
        {"filename": "t.txt", "text": "liability shall be unlimited"},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "COMPLETE"
    assert body["review_result"]["overall_risk"] == "Critical"
    assert body["review_result"]["next_action"] == "ESCALATE"
    assert Contract.objects.count() == 1


@pytest.mark.django_db
def test_create_contract_missing_text_and_file_returns_400(client):
    resp = client.post("/api/contracts/", {}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unsupported_file_type_returns_400(client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    upload = SimpleUploadedFile("contract.xyz", b"whatever", content_type="application/octet-stream")
    resp = client.post("/api/contracts/", {"file": upload}, format="multipart")
    assert resp.status_code == 400
    assert "Unsupported file type" in resp.json()["detail"]


@pytest.mark.django_db
def test_contract_detail_view(client):
    create_resp = client.post(
        "/api/contracts/", {"filename": "t.txt", "text": "no risky terms here"}, format="json"
    )
    contract_id = create_resp.json()["id"]
    resp = client.get(f"/api/contracts/{contract_id}/")
    assert resp.status_code == 200
    assert resp.json()["id"] == contract_id


@pytest.mark.django_db
def test_contract_list_view(client):
    client.post("/api/contracts/", {"filename": "a.txt", "text": "hello"}, format="json")
    client.post("/api/contracts/", {"filename": "b.txt", "text": "world"}, format="json")
    resp = client.get("/api/contracts/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.django_db
def test_oversized_text_rejected(settings, client):
    settings.MAX_UPLOAD_CHARS = 10
    resp = client.post("/api/contracts/", {"filename": "t.txt", "text": "x" * 20}, format="json")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_unauthenticated_request_rejected():
    resp = APIClient().get("/api/contracts/")
    assert resp.status_code == 401


@pytest.mark.django_db
def test_contracts_are_isolated_per_owner(client, user):
    client.post("/api/contracts/", {"filename": "alice.txt", "text": "hello"}, format="json")

    other = User.objects.create_user(username="bob", password="testpass123")
    other_client = APIClient()
    other_client.force_authenticate(user=other)

    resp = other_client.get("/api/contracts/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.django_db
def test_delete_contract(client):
    create_resp = client.post("/api/contracts/", {"filename": "t.txt", "text": "hello"}, format="json")
    contract_id = create_resp.json()["id"]

    resp = client.delete(f"/api/contracts/{contract_id}/")
    assert resp.status_code == 204
    assert Contract.objects.filter(id=contract_id).count() == 0

    assert client.get(f"/api/contracts/{contract_id}/").status_code == 404


@pytest.mark.django_db
def test_delete_contract_isolated_per_owner(client, user):
    create_resp = client.post("/api/contracts/", {"filename": "alice.txt", "text": "hello"}, format="json")
    contract_id = create_resp.json()["id"]

    other = User.objects.create_user(username="bob", password="testpass123")
    other_client = APIClient()
    other_client.force_authenticate(user=other)

    resp = other_client.delete(f"/api/contracts/{contract_id}/")
    assert resp.status_code == 404
    assert Contract.objects.filter(id=contract_id).count() == 1
