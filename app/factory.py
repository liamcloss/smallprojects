from __future__ import annotations

from app.config import Settings
from app.providers.base import ContentProvider
from app.providers.mock_provider import MockProvider
from app.services.pipeline import ContentPipeline
from app.storage import Store


def build_provider(settings: Settings, force_mock: bool | None = None) -> ContentProvider:
    use_mock = settings.mock_openai if force_mock is None else force_mock
    if use_mock:
        return MockProvider()

    # Import lazily so mock-mode tests do not require or initialise the OpenAI SDK.
    from app.providers.openai_provider import OpenAIProvider

    return OpenAIProvider(settings)


def build_pipeline(settings: Settings, force_mock: bool | None = None) -> ContentPipeline:
    provider = build_provider(settings, force_mock=force_mock)
    store = Store(settings.database_path)
    return ContentPipeline(settings=settings, provider=provider, store=store)
