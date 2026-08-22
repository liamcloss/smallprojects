from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from app.models import MetricsRequest, MetricsSummary, PostArtifact, ReviewBatch


class Store:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    emotion TEXT NOT NULL,
                    hook TEXT NOT NULL,
                    concept_json TEXT NOT NULL,
                    draft_json TEXT NOT NULL,
                    directory TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics (
                    post_id TEXT PRIMARY KEY,
                    recorded_at TEXT NOT NULL,
                    views INTEGER NOT NULL,
                    likes INTEGER NOT NULL,
                    comments INTEGER NOT NULL,
                    shares INTEGER NOT NULL,
                    saves INTEGER NOT NULL,
                    followers_gained INTEGER NOT NULL,
                    audio_used TEXT,
                    FOREIGN KEY(post_id) REFERENCES posts(post_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS review_batches (
                    batch_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    batch_json TEXT NOT NULL
                )
                """
            )

    def save_review_batch(self, batch: ReviewBatch) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO review_batches (batch_id, created_at, batch_json)
                VALUES (?, ?, ?)
                """,
                (batch.batch_id, batch.created_at.isoformat(), batch.model_dump_json()),
            )

    def get_review_batch(self, batch_id: str) -> ReviewBatch | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT batch_json FROM review_batches WHERE batch_id = ?", (batch_id,)
            ).fetchone()
        if not row:
            return None
        return ReviewBatch.model_validate_json(row[0])

    def recent_review_batches(
        self, limit: int = 10, include_archived: bool = False
    ) -> list[ReviewBatch]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT batch_json FROM review_batches
                ORDER BY created_at DESC
                """
            ).fetchall()
        batches = [ReviewBatch.model_validate_json(row[0]) for row in rows]
        if not include_archived:
            batches = [batch for batch in batches if batch.status == "active"]
        return batches[:limit]

    def archive_review_batch(self, batch_id: str) -> ReviewBatch | None:
        batch = self.get_review_batch(batch_id)
        if batch is None:
            return None
        batch.status = "archived"
        self.save_review_batch(batch)
        return batch

    def scheduled_batch_for_date(self, run_date: date) -> ReviewBatch | None:
        for batch in self.recent_review_batches(limit=500, include_archived=True):
            if (
                batch.origin == "scheduled"
                and batch.status == "active"
                and batch.context.run_date == run_date
            ):
                return batch
        return None

    def save_post(self, post: PostArtifact) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO posts
                (post_id, created_at, topic, emotion, hook, concept_json, draft_json, directory)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.post_id,
                    datetime.now(timezone.utc).isoformat(),
                    post.concept.topic,
                    post.concept.emotion,
                    post.concept.hook,
                    json.dumps(post.concept.model_dump(), ensure_ascii=False),
                    json.dumps(post.draft.model_dump(), ensure_ascii=False),
                    post.directory,
                ),
            )

    def save_metrics(self, metrics: MetricsRequest) -> MetricsSummary:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO metrics
                (post_id, recorded_at, views, likes, comments, shares, saves, followers_gained, audio_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metrics.post_id,
                    datetime.now(timezone.utc).isoformat(),
                    metrics.views,
                    metrics.likes,
                    metrics.comments,
                    metrics.shares,
                    metrics.saves,
                    metrics.followers_gained,
                    metrics.audio_used,
                ),
            )
        views = max(metrics.views, 1)
        return MetricsSummary(
            post_id=metrics.post_id,
            views=metrics.views,
            share_rate=metrics.shares / views,
            save_rate=metrics.saves / views,
            engagement_rate=(metrics.likes + metrics.comments + metrics.shares + metrics.saves) / views,
            follow_conversion=metrics.followers_gained / views,
        )

    def top_posts(self, limit: int = 10) -> list[dict]:
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT p.post_id, p.topic, p.emotion, p.hook,
                       m.views, m.likes, m.comments, m.shares, m.saves, m.followers_gained,
                       CASE WHEN m.views > 0 THEN CAST(m.shares AS REAL)/m.views ELSE 0 END AS share_rate,
                       CASE WHEN m.views > 0 THEN CAST(m.saves AS REAL)/m.views ELSE 0 END AS save_rate
                FROM posts p
                JOIN metrics m ON p.post_id = m.post_id
                ORDER BY share_rate DESC, save_rate DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
