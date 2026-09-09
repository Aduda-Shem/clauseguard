import logging

from reviews.services.chat.base import ChatClient

logger = logging.getLogger(__name__)


class ResilientChatClient(ChatClient):
    """Tries the live client first; if it raises (network error, exhausted
    quota, empty response), falls back to a secondary client -- normally
    the offline keyword-search template -- so a live-API failure degrades
    to a still-useful answer instead of a dead-end error message."""

    def __init__(self, primary: ChatClient, fallback: ChatClient):
        self._primary = primary
        self._fallback = fallback

    def answer(self, question: str, contract_text: str, findings_context: str, history: list[dict]) -> str:
        try:
            return self._primary.answer(question, contract_text, findings_context, history)
        except Exception:
            logger.warning("Live chat client failed -- falling back to template search", exc_info=True)
            return self._fallback.answer(question, contract_text, findings_context, history)
