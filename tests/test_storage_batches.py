from pathlib import Path

from app.config import Settings
from app.models import ConceptsRequest
from app.providers.mock_provider import MockProvider
from app.services.pipeline import ContentPipeline
from app.storage import Store


def make_pipeline(tmp_path: Path) -> ContentPipeline:
    settings = Settings(
        mock_openai=True,
        concept_count=6,
        output_dir=tmp_path / "output",
        database_path=tmp_path / "data" / "factory.sqlite3",
    )
    return ContentPipeline(settings, MockProvider(), Store(settings.database_path))


def test_archive_hides_batch_from_default_recent_list(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(ConceptsRequest(mock=True, use_web_context=False), mock=True)
    assert pipeline.store.recent_review_batches()[0].batch_id == batch.batch_id
    archived = pipeline.store.archive_review_batch(batch.batch_id)
    assert archived is not None and archived.status == "archived"
    assert pipeline.store.recent_review_batches() == []
    assert pipeline.store.recent_review_batches(include_archived=True)[0].status == "archived"


def test_scheduled_batch_lookup_prevents_same_day_duplicate(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(
        ConceptsRequest(mock=True, use_web_context=False), mock=True, origin="scheduled"
    )
    found = pipeline.store.scheduled_batch_for_date(batch.context.run_date)
    assert found is not None
    assert found.batch_id == batch.batch_id
