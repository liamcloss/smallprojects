from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from openai import OpenAI

from app.config import Settings
from app.models import (
    CarouselDraft,
    Concept,
    ConceptBatch,
    ContentContext,
    ContextSource,
    CurrentContextBriefing,
    RankedConceptBatch,
)
from app.prompts import CONCEPT_SYSTEM, DRAFT_SYSTEM, RANK_SYSTEM, WEB_CONTEXT_PROMPT
from app.providers.base import ContentProvider


class OpenAIProvider(ContentProvider):
    def __init__(self, settings: Settings):
        if not settings.openai_api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. Set MOCK_OPENAI=true to test without API calls."
            )
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def gather_web_context(self, context: ContentContext) -> CurrentContextBriefing:
        prompt = (
            f"{WEB_CONTEXT_PROMPT}\n\n"
            f"Today is {context.run_date.isoformat()} ({context.day_name}) in {context.region}.\n"
            f"Manual trend hints supplied by the user: {context.manual_trends or 'none'}"
        )
        response = self.client.responses.create(
            model=self.settings.text_model,
            tools=[{"type": "web_search"}],
            input=prompt,
        )
        summary = response.output_text.strip()
        dumped = response.model_dump() if hasattr(response, "model_dump") else {}
        sources: list[ContextSource] = []
        seen_urls: set[str] = set()

        def walk(value):
            if isinstance(value, dict):
                if value.get("type") == "url_citation":
                    url = value.get("url")
                    if isinstance(url, str) and url and url not in seen_urls:
                        seen_urls.add(url)
                        sources.append(
                            ContextSource(
                                source_type="current_uk_event",
                                title=value.get("title") or url,
                                url=url,
                                observed_at=datetime.now(timezone.utc),
                            )
                        )
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(dumped)
        if not sources and summary:
            sources.append(
                ContextSource(
                    source_type="current_uk_event",
                    title="OpenAI web-search context",
                    summary="Web-search briefing generated without exposed source metadata.",
                    observed_at=datetime.now(timezone.utc),
                )
            )
        return CurrentContextBriefing(summary=summary, sources=sources)

    def generate_concepts(self, context: ContentContext, count: int) -> ConceptBatch:
        payload = {
            "date": context.run_date.isoformat(),
            "day": context.day_name,
            "season": context.season,
            "region": context.region,
            "manual_trends": context.manual_trends,
            "current_context": context.web_context,
            "required_number_of_concepts": count,
        }
        response = self.client.responses.parse(
            model=self.settings.text_model,
            instructions=CONCEPT_SYSTEM,
            input=(
                "Generate the requested number of distinct candidate concepts. "
                "Use this JSON context as source material:\n" + json.dumps(payload, ensure_ascii=False)
            ),
            text_format=ConceptBatch,
        )
        if response.output_parsed is None:
            raise RuntimeError("Concept generation returned no parsed output")
        batch = response.output_parsed
        return ConceptBatch(concepts=batch.concepts[:count])

    def rank_concepts(
        self, context: ContentContext, concepts: list[Concept]
    ) -> RankedConceptBatch:
        payload = {
            "date": context.run_date.isoformat(),
            "day": context.day_name,
            "context": context.web_context,
            "concepts": [concept.model_dump() for concept in concepts],
        }
        response = self.client.responses.parse(
            model=self.settings.text_model,
            instructions=RANK_SYSTEM,
            input="Rank every concept in this JSON payload:\n" + json.dumps(payload, ensure_ascii=False),
            text_format=RankedConceptBatch,
        )
        if response.output_parsed is None:
            raise RuntimeError("Concept ranking returned no parsed output")
        return response.output_parsed

    def draft_carousel(self, context: ContentContext, concept: Concept) -> CarouselDraft:
        payload = {
            "date": context.run_date.isoformat(),
            "day": context.day_name,
            "season": context.season,
            "current_context": context.web_context,
            "concept": concept.model_dump(),
        }
        response = self.client.responses.parse(
            model=self.settings.text_model,
            instructions=DRAFT_SYSTEM,
            input="Write the carousel from this JSON brief:\n" + json.dumps(payload, ensure_ascii=False),
            text_format=CarouselDraft,
        )
        if response.output_parsed is None:
            raise RuntimeError("Carousel drafting returned no parsed output")
        return response.output_parsed

    def generate_background(self, prompt: str, destination: Path, seed_hint: int = 0) -> Path:
        enriched = (
            f"{prompt.strip()}\n\n"
            "Photorealistic editorial photography. Vertical composition. No words, letters, "
            "logos, captions or watermarks. Leave generous uncluttered negative space near the "
            "centre for later typography overlay. Avoid recognisable public figures."
        )
        result = self.client.images.generate(
            model=self.settings.image_model,
            prompt=enriched,
            size=self.settings.image_generation_size,
            quality=self.settings.image_quality,
        )
        if not result.data or not result.data[0].b64_json:
            raise RuntimeError("Image generation returned no image data")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(base64.b64decode(result.data[0].b64_json))
        return destination
