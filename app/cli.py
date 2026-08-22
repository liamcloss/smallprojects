from __future__ import annotations

import json
from typing import Annotated

import typer

from app.config import settings
from app.factory import build_pipeline
from app.models import GenerateRequest

app = typer.Typer(no_args_is_help=True)


@app.command()
def generate(
    trend: Annotated[list[str] | None, typer.Option("--trend", help="Manual trend/context hint")] = None,
    posts: Annotated[int, typer.Option("--posts", min=1, max=5)] = 3,
    web: Annotated[bool, typer.Option("--web/--no-web")] = True,
    images: Annotated[bool, typer.Option("--images/--no-images")] = True,
    mock: Annotated[bool, typer.Option("--mock/--live")] = False,
):
    """Generate a batch of publish-ready carousel folders."""
    request = GenerateRequest(
        manual_trends=trend or [],
        use_web_context=web,
        output_post_count=posts,
        generate_images=images,
        mock=mock,
    )
    result = build_pipeline(settings, force_mock=mock).run(request)
    typer.echo(json.dumps(result.model_dump(mode="json"), indent=2, ensure_ascii=False))


@app.command()
def top(limit: Annotated[int, typer.Option(min=1, max=100)] = 10):
    """Show highest-share-rate posts with recorded metrics."""
    from app.storage import Store

    typer.echo(json.dumps(Store(settings.database_path).top_posts(limit), indent=2))


if __name__ == "__main__":
    app()
