from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from app.config import Settings
from app.models import (
    CarouselDraft,
    ConceptsRequest,
    GenerateRequest,
    GenerateResponse,
    PostArtifact,
    ReviewBatch,
    ReviewItem,
)
from app.providers.base import ContentProvider
from app.services.context import make_context
from app.services.render import render_slide
from app.storage import Store


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:60] or "post"


class ContentPipeline:
    def __init__(self, settings: Settings, provider: ContentProvider, store: Store):
        self.settings = settings
        self.provider = provider
        self.store = store

    def _ranked_concepts(self, manual_trends: list[str], use_web_context: bool | None):
        context = make_context(self.settings.uk_region, manual_trends)
        use_web = self.settings.use_web_context if use_web_context is None else use_web_context
        if use_web:
            briefing = self.provider.gather_web_context(context)
            context.web_context = briefing.summary
            context.sources.extend(briefing.sources)

        batch = self.provider.generate_concepts(context, self.settings.concept_count)
        ranking = self.provider.rank_concepts(context, batch.concepts)
        concepts_by_id = {concept.id: concept for concept in batch.concepts}
        ranking_by_id = {item.concept_id: item for item in ranking.ranking}

        ordered = [
            concepts_by_id[item.concept_id]
            for item in sorted(ranking.ranking, key=lambda item: item.rank)
            if item.concept_id in concepts_by_id
        ]
        ranked_ids = {concept.id for concept in ordered}
        ordered.extend(
            sorted(
                [concept for concept in batch.concepts if concept.id not in ranked_ids],
                key=lambda c: c.weighted_score,
                reverse=True,
            )
        )
        return context, ordered, ranking_by_id

    def prepare_review(
        self,
        request: ConceptsRequest,
        mock: bool,
        origin: Literal["manual", "scheduled"] = "manual",
    ) -> ReviewBatch:
        context, ordered, ranking_by_id = self._ranked_concepts(
            request.manual_trends, request.use_web_context
        )
        selected = ordered[: request.output_post_count]
        items: list[ReviewItem] = []
        for fallback_rank, concept in enumerate(selected, start=1):
            ranking = ranking_by_id.get(concept.id)
            draft = self.provider.draft_carousel(context, concept)
            items.append(
                ReviewItem(
                    rank=ranking.rank if ranking else fallback_rank,
                    rationale=ranking.rationale if ranking else "Fallback weighted-score ranking",
                    score=concept.weighted_score,
                    concept=concept,
                    draft=draft,
                )
            )

        batch = ReviewBatch(
            batch_id=f"{context.run_date.isoformat()}-{uuid.uuid4().hex[:8]}",
            created_at=datetime.now(timezone.utc),
            context=context,
            mock=mock,
            origin=origin,
            items=items,
        )
        self.store.save_review_batch(batch)
        return batch

    def render_review_item(
        self,
        batch: ReviewBatch,
        concept_id: str,
        draft_override: CarouselDraft | None = None,
    ) -> PostArtifact:
        item = next((item for item in batch.items if item.concept.id == concept_id), None)
        if item is None:
            raise KeyError(f"Concept {concept_id!r} is not in batch {batch.batch_id!r}")

        draft = draft_override or item.draft
        concept = item.concept
        post_id = f"{batch.batch_id}-{_slug(concept.topic)}-{_slug(concept.id)}"
        post_dir = self.settings.output_dir / batch.batch_id / f"{item.rank:02d}-{_slug(concept.topic)}"
        raw_dir = post_dir / "raw"
        final_dir = post_dir / "slides"
        post_dir.mkdir(parents=True, exist_ok=True)

        slide_files: list[str] = []
        for slide in draft.slides:
            raw_path = raw_dir / f"{slide.number:02d}.png"
            final_path = final_dir / f"{slide.number:02d}.jpg"
            self.provider.generate_background(slide.visual_prompt, raw_path, seed_hint=slide.number)
            render_slide(raw_path, slide.text, slide.number, final_path, self.settings)
            slide_files.append(str(final_path.resolve()))

        (post_dir / "caption.txt").write_text(
            draft.caption + "\n\n" + " ".join(draft.hashtags), encoding="utf-8"
        )
        (post_dir / "music.txt").write_text(
            "Mood: "
            + draft.music_mood
            + "\nSearch in TikTok: "
            + ", ".join(draft.music_search_terms),
            encoding="utf-8",
        )
        metadata = {
            "post_id": post_id,
            "batch_id": batch.batch_id,
            "rank": item.rank,
            "context": batch.context.model_dump(mode="json"),
            "concept": concept.model_dump(),
            "draft": draft.model_dump(),
            "slide_files": slide_files,
        }
        (post_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        artifact = PostArtifact(
            post_id=post_id,
            concept=concept,
            draft=draft,
            directory=str(post_dir.resolve()),
            slide_files=slide_files,
        )
        self.store.save_post(artifact)
        return artifact

    def run(self, request: GenerateRequest) -> GenerateResponse:
        """Legacy all-at-once path, retained for CLI/backwards compatibility."""
        context, ordered, _ = self._ranked_concepts(request.manual_trends, request.use_web_context)
        output_count = request.output_post_count or self.settings.output_post_count
        selected = ordered[:output_count]
        run_id = f"{context.run_date.isoformat()}-{uuid.uuid4().hex[:8]}"
        run_dir = self.settings.output_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        posts: list[PostArtifact] = []
        for rank, concept in enumerate(selected, start=1):
            draft = self.provider.draft_carousel(context, concept)
            post_id = f"{run_id}-{rank:02d}-{_slug(concept.topic)}"
            post_dir = run_dir / f"{rank:02d}-{_slug(concept.topic)}"
            raw_dir = post_dir / "raw"
            final_dir = post_dir / "slides"
            post_dir.mkdir(parents=True, exist_ok=True)

            slide_files: list[str] = []
            if request.generate_images:
                for slide in draft.slides:
                    raw_path = raw_dir / f"{slide.number:02d}.png"
                    final_path = final_dir / f"{slide.number:02d}.jpg"
                    self.provider.generate_background(slide.visual_prompt, raw_path, seed_hint=slide.number)
                    render_slide(raw_path, slide.text, slide.number, final_path, self.settings)
                    slide_files.append(str(final_path.resolve()))

            (post_dir / "caption.txt").write_text(
                draft.caption + "\n\n" + " ".join(draft.hashtags), encoding="utf-8"
            )
            (post_dir / "music.txt").write_text(
                "Mood: " + draft.music_mood + "\nSearch in TikTok: " + ", ".join(draft.music_search_terms),
                encoding="utf-8",
            )
            (post_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "post_id": post_id,
                        "rank": rank,
                        "context": context.model_dump(mode="json"),
                        "concept": concept.model_dump(),
                        "draft": draft.model_dump(),
                        "slide_files": slide_files,
                    },
                    indent=2,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            artifact = PostArtifact(
                post_id=post_id,
                concept=concept,
                draft=draft,
                directory=str(post_dir.resolve()),
                slide_files=slide_files,
            )
            self.store.save_post(artifact)
            posts.append(artifact)

        response = GenerateResponse(
            run_id=run_id,
            created_at=datetime.now(timezone.utc),
            context=context,
            posts=posts,
        )
        (run_dir / "run.json").write_text(response.model_dump_json(indent=2), encoding="utf-8")
        return response
