from django.conf import settings


def is_llm_configured() -> bool:
    return bool(settings.GEMINI_API_KEY)
