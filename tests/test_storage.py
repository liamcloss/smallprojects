from pathlib import Path

from app.config import Settings
from app.models import ConceptsRequest
from app.providers.mock_provider import MockProvider
from app.services.pipeline import ContentPipeline
from app.storage import Store


def make_pipeline(tmp_path: Path) -> ContentPipeline:
    settings = Settings(
        mock_openai=True,
        use_web_context=True,
        concept_count=6,
        output_post_count=3,
        output_dir=tmp_path / "output",
        database_path=tmp_path / "data" / "factory.sqlite3",
    )
    return ContentPipeline(settings, MockProvider(), Store(settings.database_path))


def test_context_keeps_calendar_manual_and_sourced_current_context_separate(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(
        ConceptsRequest(
            mock=True,
            manual_trends=["Back-to-school week"],
            output_post_count=3,
            use_web_context=True,
        ),
        mock=True,
    )

    source_types = {source.source_type for source in batch.context.sources}
    assert "calendar" in source_types
    assert "manual_hint" in source_types
    assert "current_uk_event" in source_types
    assert "tiktok_trend" not in source_types


def test_archived_batches_drop_out_of_recent_and_scheduled_batch_can_be_detected(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(
        ConceptsRequest(mock=True, output_post_count=3, use_web_context=False),
        mock=True,
        origin="scheduled",
    )

    assert pipeline.store.scheduled_batch_for_date(batch.context.run_date).batch_id == batch.batch_id
    archived = pipeline.store.archive_review_batch(batch.batch_id)
    assert archived is not None and archived.status == "archived"
    assert pipeline.store.recent_review_batches() == []
    assert pipeline.store.scheduled_batch_for_date(batch.context.run_date) is None
