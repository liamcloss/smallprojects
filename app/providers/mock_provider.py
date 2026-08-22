from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from app.models import (
    CarouselDraft,
    Concept,
    ConceptBatch,
    ContentContext,
    ContextSource,
    CurrentContextBriefing,
    RankedConcept,
    RankedConceptBatch,
    Slide,
)
from app.providers.base import ContentProvider


class MockProvider(ContentProvider):
    """Deterministic local provider used by tests and first-run smoke checks."""

    def gather_web_context(self, context: ContentContext) -> CurrentContextBriefing:
        summary = (
            f"Mock current context for {context.day_name}. People are moving between weekend "
            "and work routines; late-summer evenings are getting shorter."
        )
        return CurrentContextBriefing(
            summary=summary,
            sources=[
                ContextSource(
                    source_type="current_uk_event",
                    title="Mock current UK context",
                    summary=summary,
                )
            ],
        )

    def generate_concepts(self, context: ContentContext, count: int) -> ConceptBatch:
        templates = [
            ("sunday-work", "Work", "The weekend isn't too short. Your week is too expensive.", "dread"),
            ("time-passing", "Life", "One day, this ordinary Saturday will be the memory.", "nostalgia"),
            ("starting-again", "Self", "You do not need Monday to start again.", "resolve"),
            ("friendships", "Friendship", "Some friendships end without anyone doing anything wrong.", "acceptance"),
            ("parenthood", "Parenthood", "The days feel long because the years are moving quickly.", "tenderness"),
            ("comparison", "Self", "You are comparing your Tuesday to someone else's highlight reel.", "perspective"),
        ]
        concepts: list[Concept] = []
        for i in range(count):
            slug, topic, hook, emotion = templates[i % len(templates)]
            concepts.append(
                Concept(
                    id=f"{slug}-{i+1}",
                    topic=topic,
                    hook=hook,
                    emotion=emotion,
                    angle=f"A specific {emotion} observation rooted in an ordinary UK day.",
                    timeliness_score=8 - (i % 3),
                    relatability_score=9 - (i % 2),
                    shareability_score=9 - (i % 3),
                    curiosity_score=8,
                    risk_score=2,
                )
            )
        return ConceptBatch(concepts=concepts)

    def rank_concepts(
        self, context: ContentContext, concepts: list[Concept]
    ) -> RankedConceptBatch:
        ordered = sorted(concepts, key=lambda c: c.weighted_score, reverse=True)
        return RankedConceptBatch(
            ranking=[
                RankedConcept(concept_id=c.id, rank=i + 1, rationale="Mock weighted-score rank")
                for i, c in enumerate(ordered)
            ]
        )

    def draft_carousel(self, context: ContentContext, concept: Concept) -> CarouselDraft:
        lines = [
            concept.hook,
            "Because two days of breathing room cannot fix five days of running on empty.",
            "You can be grateful for your job and still notice what it is costing you.",
            "Sometimes the problem is not motivation. It is how little of the week feels yours.",
            "A good life should not begin every Friday night and disappear every Sunday.",
            "Build a week you do not have to keep escaping from.",
        ]
        prompts = [
            "Rain on the window of a quiet British train at dusk, lone commuter silhouette",
            "Unmade bed in soft Sunday evening light, realistic small UK bedroom",
            "Office building windows after sunset, one floor still lit, realistic photograph",
            "Quiet kitchen table with mug and keys, late evening natural light",
            "Empty suburban street at blue hour after rain, UK terraced houses",
            "Early morning footpath with first warm light, ordinary British neighbourhood",
        ]
        return CarouselDraft(
            title=concept.hook,
            slides=[
                Slide(number=i + 1, text=lines[i], visual_prompt=prompts[i]) for i in range(6)
            ],
            caption="Maybe the goal is not to survive the week better.",
            hashtags=["#worklife", "#sundayscaries", "#lifequotes", "#relatable"],
            music_mood="reflective, restrained, slightly nostalgic",
            music_search_terms=["nostalgic slowed", "reflective acoustic", "late night edit"],
        )

    def generate_background(self, prompt: str, destination: Path, seed_hint: int = 0) -> Path:
        width, height = 1024, 1536
        image = Image.new("RGB", (width, height), (32 + seed_hint * 7, 42, 54 + seed_hint * 5))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            value = int(20 + 45 * (y / height))
            draw.line((0, y, width, y), fill=(value, value + 8, value + 18))
        draw.ellipse((120, 180, 900, 960), fill=(52, 62, 74))
        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(destination, format="PNG")
        return destination
