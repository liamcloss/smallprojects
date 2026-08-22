from pathlib import Path

from PIL import Image

from app.config import Settings
from app.services.render import render_slide


def test_render_slide(tmp_path: Path):
    background = tmp_path / "bg.png"
    Image.new("RGB", (1024, 1536), (50, 60, 70)).save(background)
    output = tmp_path / "slide.jpg"
    settings = Settings(output_dir=tmp_path / "out", database_path=tmp_path / "db.sqlite3")

    render_slide(
        background,
        "Build a week you do not have to keep escaping from.",
        6,
        output,
        settings,
    )

    rendered = Image.open(output)
    assert rendered.size == (1080, 1920)
