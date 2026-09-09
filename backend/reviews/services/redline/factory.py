from django.conf import settings

from reviews.services.llm_config import is_llm_configured
from reviews.services.redline.base import RedlineClient
from reviews.services.redline.gemini_client import GeminiRedlineClient
from reviews.services.redline.template import TemplateRedlineClient


def get_redline_client() -> RedlineClient:
    if is_llm_configured():
        return GeminiRedlineClient(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    return TemplateRedlineClient()
