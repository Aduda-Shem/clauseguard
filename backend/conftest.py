import pytest


@pytest.fixture(autouse=True)
def _no_live_llm_calls_in_tests(settings):
    """Tests must be deterministic, free, and offline regardless of whatever
    real API key is configured in .env for actual app usage -- force the
    template/fallback path everywhere unless a test explicitly opts back in."""
    settings.GEMINI_API_KEY = ""
