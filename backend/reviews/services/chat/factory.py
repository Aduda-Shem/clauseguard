from django.conf import settings

from reviews.services.chat.base import ChatClient
from reviews.services.chat.gemini_client import GeminiChatClient
from reviews.services.chat.resilient import ResilientChatClient
from reviews.services.chat.template import TemplateChatClient
from reviews.services.llm_config import is_llm_configured


def get_chat_client() -> ChatClient:
    if is_llm_configured():
        return ResilientChatClient(
            primary=GeminiChatClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL),
            fallback=TemplateChatClient(),
        )
    return TemplateChatClient()
