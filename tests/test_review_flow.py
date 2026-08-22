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
        account_handle="@test",
    )
    return ContentPipeline(settings, MockProvider(), Store(settings.database_path))


def test_prepare_review_creates_three_editable_drafts_without_images(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(
        ConceptsRequest(mock=True, output_post_count=3, use_web_context=True), mock=True
    )

    assert len(batch.items) == 3
    assert all(len(item.draft.slides) == 6 for item in batch.items)
    assert pipeline.store.get_review_batch(batch.batch_id) is not None
    assert not (pipeline.settings.output_dir / batch.batch_id).exists()


def test_render_review_item_only_renders_selected_post(tmp_path: Path):
    pipeline = make_pipeline(tmp_path)
    batch = pipeline.prepare_review(
        ConceptsRequest(mock=True, output_post_count=3, use_web_context=True), mock=True
    )

    selected = batch.items[1]
    post = pipeline.render_review_item(batch, selected.concept.id)

    assert len(post.slide_files) == 6
    assert all(Path(path).exists() for path in post.slide_files)
    assert (Path(post.directory) / "caption.txt").exists()
    assert (Path(post.directory) / "music.txt").exists()
    rendered_post_dirs = list((pipeline.settings.output_dir / batch.batch_id).glob("*"))
    assert len(rendered_post_dirs) == 1
