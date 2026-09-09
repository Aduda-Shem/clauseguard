import io

import pytest
from django.contrib.auth.models import User
from pypdf import PdfReader
from rest_framework.test import APIClient

from reviews.models import Contract


@pytest.mark.django_db
def test_report_pdf_returns_pdf_for_completed_review(client):
    create_resp = client.post(
        "/api/contracts/",
        {"filename": "risky & <weird> \"quotes\".txt", "text": "liability shall be unlimited"},
        format="json",
    )
    contract_id = create_resp.json()["id"]

    resp = client.get(f"/api/contracts/{contract_id}/report.pdf")

    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert "attachment;" in resp["Content-Disposition"]
    assert resp.content.startswith(b"%PDF")


@pytest.mark.django_db
def test_report_pdf_does_not_double_escape_table_header(client):
    """The findings-table header is passed straight to reportlab's Table, which
    renders raw strings as plain text rather than parsing XML entities the way
    Paragraph does -- a literal '&amp;' in the header source rendered as the
    literal text 'Finding &amp; suggested redline' instead of an ampersand."""
    create_resp = client.post(
        "/api/contracts/", {"filename": "t.txt", "text": "liability shall be unlimited"}, format="json"
    )
    contract_id = create_resp.json()["id"]

    resp = client.get(f"/api/contracts/{contract_id}/report.pdf")
    text = "".join(page.extract_text() for page in PdfReader(io.BytesIO(resp.content)).pages)

    assert "&amp;" not in text
    assert "Finding & suggested redline" in text


@pytest.mark.django_db
def test_report_pdf_exposes_content_disposition_to_cross_origin_js(client, settings):
    """The frontend runs on a different origin (5174 vs 8001) and reads
    Content-Disposition via JS to name the downloaded file -- browsers hide
    that header from cross-origin JS unless the server explicitly exposes it.
    Regression test for a real bug: the download worked, but silently fell
    back to a generic filename because this wasn't set."""
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:5174"]
    create_resp = client.post("/api/contracts/", {"filename": "a.txt", "text": "hello"}, format="json")
    contract_id = create_resp.json()["id"]

    resp = client.get(f"/api/contracts/{contract_id}/report.pdf", HTTP_ORIGIN="http://localhost:5174")

    assert "Content-Disposition" in resp["Access-Control-Expose-Headers"]


@pytest.mark.django_db
def test_report_pdf_404s_for_missing_or_other_owner_contract(client, user):
    resp = client.get("/api/contracts/999999/report.pdf")
    assert resp.status_code == 404

    create_resp = client.post("/api/contracts/", {"filename": "a.txt", "text": "hello"}, format="json")
    contract_id = create_resp.json()["id"]

    other = User.objects.create_user(username="bob", password="testpass123")
    other_client = APIClient()
    other_client.force_authenticate(user=other)
    assert other_client.get(f"/api/contracts/{contract_id}/report.pdf").status_code == 404


@pytest.mark.django_db
def test_report_pdf_400s_before_review_completes(client, user):
    contract = Contract.objects.create(owner=user, filename="pending.txt", source_text="...", status=Contract.Status.PENDING)
    resp = client.get(f"/api/contracts/{contract.id}/report.pdf")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_report_pdf_unauthenticated_rejected():
    resp = APIClient().get("/api/contracts/1/report.pdf")
    assert resp.status_code == 401
