from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import (
    CarouselDraft, Concept, ConceptBatch, ContentContext, CurrentContextBriefing, RankedConceptBatch
)


class ContentProvider(ABC):
    @abstractmethod
    def gather_web_context(self, context: ContentContext) -> CurrentContextBriefing:
        raise NotImplementedError

    @abstractmethod
    def generate_concepts(self, context: ContentContext, count: int) -> ConceptBatch:
        raise NotImplementedError

    @abstractmethod
    def rank_concepts(
        self, context: ContentContext, concepts: list[Concept]
    ) -> RankedConceptBatch:
        raise NotImplementedError

    @abstractmethod
    def draft_carousel(self, context: ContentContext, concept: Concept) -> CarouselDraft:
        raise NotImplementedError

    @abstractmethod
    def generate_background(self, prompt: str, destination: Path, seed_hint: int = 0) -> Path:
        raise NotImplementedError
