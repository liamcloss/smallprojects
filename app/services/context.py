from __future__ import annotations

from datetime import date, datetime, timezone

from app.models import ContentContext, ContextSource


def uk_season(day: date) -> str:
    month = day.month
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    return "autumn"


def make_context(region: str, manual_trends: list[str] | None = None) -> ContentContext:
    today = date.today()
    hints = manual_trends or []
    now = datetime.now(timezone.utc)
    sources = [
        ContextSource(
            source_type="calendar",
            title=f"{today.strftime('%A')} {today.isoformat()}",
            summary=f"{uk_season(today).title()} calendar context for {region}.",
            observed_at=now,
        )
    ]
    sources.extend(
        ContextSource(
            source_type="manual_hint",
            title=hint,
            summary="User-supplied context hint; not independently verified as a trend.",
            observed_at=now,
        )
        for hint in hints
    )
    return ContentContext(
        run_date=today,
        day_name=today.strftime("%A"),
        season=uk_season(today),
        region=region,
        manual_trends=hints,
        sources=sources,
    )
