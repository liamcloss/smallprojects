from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auth import authorised_basic_header
from app.config import settings
from app.factory import build_pipeline
from app.models import (
    ConceptsRequest,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    MetricsRequest,
    MetricsSummary,
    RenderDraftRequest,
    RenderResponse,
    ReviewBatch,
)
from app.scheduler import auto_prepare_loop
from app.storage import Store

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
settings.output_dir.mkdir(parents=True, exist_ok=True)
settings.database_path.parent.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
store = Store(settings.database_path)


def _public_error(exc: Exception) -> str:
    message = str(exc)
    if isinstance(exc, RuntimeError) and (
        "OPENAI_API_KEY" in message
        or "returned no" in message
        or "Carousel" in message
        or "Slide" in message
    ):
        return message
    return "Request failed. Check the HEX container logs for details."


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = None
    if settings.auto_prepare_enabled:
        task = asyncio.create_task(auto_prepare_loop(settings))
    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(
    title="TikTok Content Factory",
    version="0.2.0",
    description="Generate, review and render six-slide TikTok quote carousels.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/output", StaticFiles(directory=str(settings.output_dir), check_dir=False), name="output")


@app.middleware("http")
async def optional_basic_auth(request: Request, call_next):
    if request.url.path in {"/health"} or request.url.path.startswith("/static/"):
        return await call_next(request)
    if not authorised_basic_header(
        request.headers.get("authorization"),
        settings.app_auth_username,
        settings.app_auth_password,
    ):
        return Response(
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="TikTok Content Factory"'},
        )
    return await call_next(request)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "has_api_key": bool(settings.openai_api_key),
            "mock_default": settings.mock_openai or not bool(settings.openai_api_key),
            "text_model": settings.text_model,
            "image_model": settings.image_model,
        },
    )


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        mock_openai=settings.mock_openai,
        has_api_key=bool(settings.openai_api_key),
        text_model=settings.text_model,
        image_model=settings.image_model,
    )


@app.post("/concepts", response_model=ReviewBatch)
def concepts(request: ConceptsRequest) -> ReviewBatch:
    force_mock = settings.mock_openai if request.mock is None else request.mock
    try:
        pipeline = build_pipeline(settings, force_mock=force_mock)
        return pipeline.prepare_review(request, mock=force_mock)
    except Exception as exc:
        logger.exception("Concept generation failed")
        raise HTTPException(status_code=500, detail=_public_error(exc)) from exc


@app.get("/drafts/{batch_id}", response_model=ReviewBatch)
def get_draft_batch(batch_id: str) -> ReviewBatch:
    batch = store.get_review_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Draft batch not found")
    return batch


@app.get("/drafts", response_model=list[ReviewBatch])
def recent_drafts(
    limit: int = Query(default=10, ge=1, le=50),
    include_archived: bool = False,
) -> list[ReviewBatch]:
    return store.recent_review_batches(limit, include_archived=include_archived)


@app.post("/drafts/{batch_id}/archive", response_model=ReviewBatch)
def archive_draft_batch(batch_id: str) -> ReviewBatch:
    batch = store.archive_review_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Draft batch not found")
    return batch


@app.post("/drafts/{batch_id}/{concept_id}/render", response_model=RenderResponse)
def render_draft(batch_id: str, concept_id: str, request: RenderDraftRequest) -> RenderResponse:
    batch = store.get_review_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Draft batch not found")
    try:
        pipeline = build_pipeline(settings, force_mock=batch.mock)
        post = pipeline.render_review_item(batch, concept_id, request.draft)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Draft rendering failed")
        raise HTTPException(status_code=500, detail=_public_error(exc)) from exc

    output_root = settings.output_dir.resolve()
    urls: list[str] = []
    for slide_file in post.slide_files:
        relative = Path(slide_file).resolve().relative_to(output_root)
        urls.append("/output/" + relative.as_posix())
    return RenderResponse(post=post, slide_urls=urls)


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    """Legacy all-at-once endpoint. Prefer /concepts + approval + /render."""
    try:
        pipeline = build_pipeline(settings, force_mock=request.mock)
        return pipeline.run(request)
    except Exception as exc:
        logger.exception("Legacy generation failed")
        raise HTTPException(status_code=500, detail=_public_error(exc)) from exc


@app.post("/metrics", response_model=MetricsSummary)
def save_metrics(request: MetricsRequest) -> MetricsSummary:
    return store.save_metrics(request)


@app.get("/metrics/top")
def top_metrics(limit: int = Query(default=10, ge=1, le=100)) -> list[dict]:
    return store.top_posts(limit=limit)
