from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import Settings
from app.factory import build_pipeline
from app.models import ConceptsRequest

logger = logging.getLogger(__name__)


def next_run(now: datetime, hhmm: str, timezone_name: str) -> datetime:
    tz = ZoneInfo(timezone_name)
    local_now = now.astimezone(tz)
    hour, minute = (int(part) for part in hhmm.split(":", 1))
    target = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= local_now:
        target += timedelta(days=1)
    return target


async def auto_prepare_loop(settings: Settings) -> None:
    """Prepare three text drafts daily. Rendering remains explicitly human-approved."""
    while True:
        now = datetime.now(ZoneInfo(settings.auto_prepare_timezone))
        target = next_run(now, settings.auto_prepare_time, settings.auto_prepare_timezone)
        await asyncio.sleep(max((target - now).total_seconds(), 1))
        try:
            pipeline = build_pipeline(settings, force_mock=settings.auto_prepare_mock)
            run_date = target.date()
            existing = pipeline.store.scheduled_batch_for_date(run_date)
            if existing is not None:
                logger.info(
                    "Skipping scheduled TikTok draft preparation; active batch already exists for %s",
                    run_date,
                )
                continue
            batch = pipeline.prepare_review(
                ConceptsRequest(
                    manual_trends=[],
                    use_web_context=settings.auto_prepare_web_context,
                    output_post_count=3,
                    mock=settings.auto_prepare_mock,
                ),
                mock=settings.auto_prepare_mock,
                origin="scheduled",
            )
            logger.info("Prepared scheduled TikTok draft batch %s", batch.batch_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Scheduled TikTok draft preparation failed")
