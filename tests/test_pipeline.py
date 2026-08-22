from pathlib import Path

from app.config import Settings
from app.models import GenerateRequest
from app.providers.mock_provider import MockProvider
from app.services.pipeline import ContentPipeline
from app.storage import Store


def test_pipeline_creates_three_posts(tmp_path: Path):
    settings = Settings(
        mock_openai=True,
        use_web_context=True,
        concept_count=6,
        output_post_count=3,
        output_dir=tmp_path / "output",
        database_path=tmp_path / "data" / "factory.sqlite3",
        account_handle="@test",
    )
    pipeline = ContentPipeline(settings, MockProvider(), Store(settings.database_path))
    result = pipeline.run(GenerateRequest(mock=True, output_post_count=3, generate_images=True))

    assert len(result.posts) == 3
    for post in result.posts:
        assert len(post.slide_files) == 6
        assert (Path(post.directory) / "caption.txt").exists()
        assert (Path(post.directory) / "metadata.json").exists()
