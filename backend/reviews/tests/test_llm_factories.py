import json

import pytest

from reviews.services.chat.factory import get_chat_client
from reviews.services.chat.gemini_client import GeminiChatClient
from reviews.services.chat.resilient import ResilientChatClient
from reviews.services.chat.template import TemplateChatClient
from reviews.services.llm_config import is_llm_configured
from reviews.services.redline.base import RedlineRequest
from reviews.services.redline.factory import get_redline_client
from reviews.services.redline.gemini_client import GeminiRedlineClient, _RedlineSchema
from reviews.services.redline.template import TemplateRedlineClient


def _fake_item(rule_key, redline):
    return type("Item", (), {"rule_key": rule_key, "redline": redline})()


def test_no_key_configured_uses_template(settings):
    assert isinstance(get_redline_client(), TemplateRedlineClient)
    assert isinstance(get_chat_client(), TemplateChatClient)
    assert is_llm_configured() is False


def test_gemini_key_selects_gemini(settings):
    settings.GEMINI_API_KEY = "fake-gemini-key"
    assert isinstance(get_redline_client(), GeminiRedlineClient)

    chat_client = get_chat_client()
    assert isinstance(chat_client, ResilientChatClient)
    assert isinstance(chat_client._primary, GeminiChatClient)
    assert isinstance(chat_client._fallback, TemplateChatClient)
    assert is_llm_configured() is True


def test_template_redline_client_returns_fallback_text_unchanged():
    client = TemplateRedlineClient()
    requests = [RedlineRequest(rule_key="k1", category="Liability", matched_text="x", reason="y", fallback="cap it")]
    result = client.draft(requests, "1 Critical-risk item(s): Liability.")
    assert result.redlines == {"k1": "cap it"}
    assert result.summary == "1 Critical-risk item(s): Liability."


def test_gemini_redline_client_makes_exactly_one_call_for_multiple_findings(monkeypatch):
    """The whole point of batching: N findings must cost 1 API call, not N
    -- this is what makes a review usable under a 5-requests/minute free
    tier instead of exhausting it by itself. See docs/EVALUATION.md."""
    call_count = {"n": 0}

    class FakeParsed:
        redlines = [
            _fake_item("k1", "Negotiate X."),
            _fake_item("k2", "Negotiate Y."),
            _fake_item("k3", "Negotiate Z."),
        ]
        summary = "Overall, sign with conditions."

    def fake_generate_content(**kwargs):
        call_count["n"] += 1
        return type("Resp", (), {"parsed": FakeParsed()})()

    client = GeminiRedlineClient("fake-key", "fake-model")
    monkeypatch.setattr(client._client.models, "generate_content", fake_generate_content)

    requests = [
        RedlineRequest(rule_key="k1", category="Liability", matched_text="a", reason="r1", fallback="f1"),
        RedlineRequest(rule_key="k2", category="Payment", matched_text="b", reason="r2", fallback="f2"),
        RedlineRequest(rule_key="k3", category="Auto-renewal", matched_text="c", reason="r3", fallback="f3"),
    ]
    result = client.draft(requests, "findings summary")

    assert call_count["n"] == 1
    assert result.redlines == {"k1": "Negotiate X.", "k2": "Negotiate Y.", "k3": "Negotiate Z."}
    assert result.summary == "Overall, sign with conditions."


def test_gemini_redline_client_skips_call_when_nothing_flagged(monkeypatch):
    def fail_if_called(**kwargs):
        raise AssertionError("should not call the API when there are no Medium+ findings")

    client = GeminiRedlineClient("fake-key", "fake-model")
    monkeypatch.setattr(client._client.models, "generate_content", fail_if_called)

    result = client.draft([], "No Medium, High, or Critical risk clauses were found.")
    assert result.redlines == {}
    assert result.summary == "No Medium, High, or Critical risk clauses were found."


def test_gemini_redline_client_falls_back_per_finding_on_error(monkeypatch):
    client = GeminiRedlineClient("fake-key", "fake-model")
    monkeypatch.setattr(
        client._client.models, "generate_content", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    requests = [RedlineRequest(rule_key="k1", category="Liability", matched_text="x", reason="y", fallback="cap it")]
    result = client.draft(requests, "1 Critical-risk item(s): Liability.")
    assert result.redlines == {"k1": "cap it"}
    assert result.summary == "1 Critical-risk item(s): Liability."


def test_gemini_redline_client_disables_thinking_mode(monkeypatch):
    """Regression test: 'thinking' models can spend the entire token budget
    on internal reasoning and return no parsed output unless thinking is
    explicitly disabled -- found by hand against a real key, not by any
    test, so this locks the fix in."""
    captured = {}

    class FakeParsed:
        redlines = [_fake_item("k1", "ok")]
        summary = "ok"

    def fake_generate_content(**kwargs):
        captured.update(kwargs)
        return type("Resp", (), {"parsed": FakeParsed()})()

    client = GeminiRedlineClient("fake-key", "fake-model")
    monkeypatch.setattr(client._client.models, "generate_content", fake_generate_content)
    requests = [RedlineRequest(rule_key="k1", category="Liability", matched_text="x", reason="y", fallback="f")]
    client.draft(requests, "summary")

    assert captured["config"].thinking_config.thinking_budget == 0


def test_gemini_chat_client_raises_on_error(monkeypatch):
    client = GeminiChatClient("fake-key", "fake-model")
    monkeypatch.setattr(
        client._client.models, "generate_content", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    with pytest.raises(RuntimeError):
        client.answer("What are the payment terms?", "contract text", "no findings", [])


def test_redline_schema_has_no_additional_properties():
    """Gemini's structured-output schema rejects open-ended maps like
    dict[str, str] ('additionalProperties is not supported in the Gemini
    API') -- a real error found by hand against a real key, which every
    other test here missed because they mock `generate_content` entirely,
    bypassing the schema-conversion step where the failure actually
    happened. This test exercises that shape directly, without a network
    call, so a future field addition can't silently reintroduce it."""
    schema_json = json.dumps(_RedlineSchema.model_json_schema())
    assert "additionalProperties" not in schema_json


def test_resilient_chat_client_falls_back_to_template_on_primary_failure():
    class AlwaysFailsClient:
        def answer(self, *args, **kwargs):
            raise RuntimeError("quota exceeded")

    client = ResilientChatClient(primary=AlwaysFailsClient(), fallback=TemplateChatClient())
    text = "Payment terms are net 90 from invoice date."
    answer = client.answer("what are the payment terms?", text, "", [])
    assert "net 90" in answer
    assert "keyword-matched" in answer.lower()
