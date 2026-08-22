from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ContextSource(BaseModel):
    source_type: Literal["calendar", "manual_hint", "current_uk_event", "tiktok_trend"]
    title: str
    summary: str = ""
    url: str | None = None
    observed_at: datetime | None = None


class CurrentContextBriefing(BaseModel):
    summary: str = ""
    sources: list[ContextSource] = Field(default_factory=list)


class ContentContext(BaseModel):
    run_date: date
    day_name: str
    season: str
    region: str
    manual_trends: list[str] = Field(default_factory=list)
    web_context: str = ""
    sources: list[ContextSource] = Field(default_factory=list)


class Concept(BaseModel):
    id: str = Field(description="Short stable slug-like identifier")
    topic: str
    hook: str
    emotion: str
    angle: str
    timeliness_score: int = Field(ge=1, le=10)
    relatability_score: int = Field(ge=1, le=10)
    shareability_score: int = Field(ge=1, le=10)
    curiosity_score: int = Field(ge=1, le=10)
    risk_score: int = Field(ge=1, le=10, description="10 means high risk or likely to age badly")

    @property
    def weighted_score(self) -> float:
        return round(
            self.shareability_score * 0.30
            + self.relatability_score * 0.30
            + self.curiosity_score * 0.20
            + self.timeliness_score * 0.20
            - self.risk_score * 0.08,
            2,
        )


class ConceptBatch(BaseModel):
    concepts: list[Concept]


class RankedConcept(BaseModel):
    concept_id: str
    rank: int = Field(ge=1)
    rationale: str


class RankedConceptBatch(BaseModel):
    ranking: list[RankedConcept]


class Slide(BaseModel):
    number: int = Field(ge=1, le=6)
    text: str
    visual_prompt: str

    @field_validator("text")
    @classmethod
    def validate_word_count(cls, value: str) -> str:
        words = value.split()
        if len(words) > 22:
            raise ValueError("Slide text must be 22 words or fewer")
        return value.strip()


class CarouselDraft(BaseModel):
    title: str
    slides: list[Slide]
    caption: str
    hashtags: list[str]
    music_mood: str
    music_search_terms: list[str]

    @field_validator("slides")
    @classmethod
    def exactly_six_slides(cls, value: list[Slide]) -> list[Slide]:
        if len(value) != 6:
            raise ValueError("Carousel must contain exactly six slides")
        numbers = [slide.number for slide in value]
        if numbers != [1, 2, 3, 4, 5, 6]:
            raise ValueError("Slides must be numbered 1 through 6")
        return value


class GenerateRequest(BaseModel):
    manual_trends: list[str] = Field(default_factory=list)
    use_web_context: bool | None = None
    output_post_count: int | None = Field(default=None, ge=1, le=5)
    generate_images: bool = True
    mock: bool | None = None


class ConceptsRequest(BaseModel):
    manual_trends: list[str] = Field(default_factory=list)
    use_web_context: bool | None = None
    output_post_count: int = Field(default=3, ge=1, le=5)
    mock: bool | None = None


class ReviewItem(BaseModel):
    rank: int
    rationale: str
    score: float
    concept: Concept
    draft: CarouselDraft


class ReviewBatch(BaseModel):
    batch_id: str
    created_at: datetime
    context: ContentContext
    mock: bool
    origin: Literal["manual", "scheduled"] = "manual"
    status: Literal["active", "archived"] = "active"
    items: list[ReviewItem]


class RenderDraftRequest(BaseModel):
    draft: CarouselDraft | None = None


class PostArtifact(BaseModel):
    post_id: str
    concept: Concept
    draft: CarouselDraft
    directory: str
    slide_files: list[str]


class RenderResponse(BaseModel):
    post: PostArtifact
    slide_urls: list[str]


class GenerateResponse(BaseModel):
    run_id: str
    created_at: datetime
    context: ContentContext
    posts: list[PostArtifact]


class MetricsRequest(BaseModel):
    post_id: str
    views: int = Field(ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    saves: int = Field(default=0, ge=0)
    followers_gained: int = Field(default=0, ge=0)
    audio_used: str | None = None


class MetricsSummary(BaseModel):
    post_id: str
    views: int
    share_rate: float
    save_rate: float
    engagement_rate: float
    follow_conversion: float


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    mock_openai: bool
    has_api_key: bool
    text_model: str
    image_model: str
