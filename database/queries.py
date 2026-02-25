"""
PASIS Database Query Helpers
Common analytical queries following data-archivist SKILL.md standards
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from database.models import MarketSignal, WeeklyReport

log = logging.getLogger(__name__)


def get_signals_df(
    session: Session,
    scope: Optional[str] = None,
    days_back: int = 90,
    limit: int = 500,
) -> pd.DataFrame:
    """Return signals as DataFrame for Streamlit visualization."""
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    query = session.query(MarketSignal).filter(
        MarketSignal.published_at >= cutoff
    )
    if scope:
        query = query.filter(MarketSignal.scope == scope)
    query = query.order_by(MarketSignal.published_at.desc()).limit(limit)

    rows = query.all()
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame([
        {
            "event_id": r.event_id,
            "scope": r.scope,
            "category": r.category,
            "title": r.title,
            "summary": r.summary,
            "strategic_implication": r.strategic_implication,
            "publisher": r.publisher,
            "source_url": r.source_url,
            "published_at": r.published_at,
            "confidence_score": r.confidence_score,
            "data_quality_score": r.data_quality_score,
        }
        for r in rows
    ])


def get_kpi_metrics(session: Session) -> dict:
    """Return KPI summary for dashboard header."""
    total = session.query(func.count(MarketSignal.id)).scalar() or 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week = session.query(func.count(MarketSignal.id)).filter(
        MarketSignal.scraped_at >= week_ago
    ).scalar() or 0

    avg_confidence = session.query(
        func.avg(MarketSignal.confidence_score)
    ).filter(MarketSignal.confidence_score.isnot(None)).scalar() or 0.0

    scope_counts = dict(
        session.query(MarketSignal.scope, func.count(MarketSignal.id))
        .group_by(MarketSignal.scope)
        .all()
    )

    return {
        "total_signals": total,
        "this_week": this_week,
        "avg_confidence": round(float(avg_confidence), 2),
        "scope_counts": scope_counts,
        "market": scope_counts.get("Market", 0),
        "tech": scope_counts.get("Tech", 0),
        "case": scope_counts.get("Case", 0),
        "policy": scope_counts.get("Policy", 0),
    }


def get_timeline_data(session: Session, days_back: int = 90) -> pd.DataFrame:
    """Weekly signal volume by scope for trend chart."""
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    rows = session.query(
        MarketSignal.scope,
        MarketSignal.published_at,
    ).filter(
        MarketSignal.published_at >= cutoff
    ).all()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["scope", "published_at"])
    df["week"] = pd.to_datetime(df["published_at"]).dt.to_period("W").dt.start_time
    return df.groupby(["week", "scope"]).size().reset_index(name="count")


def get_top_publishers(session: Session, limit: int = 10) -> pd.DataFrame:
    """Top publishers by signal count."""
    rows = session.query(
        MarketSignal.publisher,
        func.count(MarketSignal.id).label("count"),
        func.avg(MarketSignal.confidence_score).label("avg_confidence"),
    ).filter(
        MarketSignal.publisher.isnot(None)
    ).group_by(MarketSignal.publisher).order_by(
        func.count(MarketSignal.id).desc()
    ).limit(limit).all()

    return pd.DataFrame(rows, columns=["publisher", "count", "avg_confidence"])


def get_latest_weekly_report(session: Session) -> Optional[WeeklyReport]:
    """Return most recent weekly report."""
    return session.query(WeeklyReport).order_by(
        WeeklyReport.week_start.desc()
    ).first()


def get_news_feed_df(
    session: Session,
    company: str | None = None,
    days_back: int = 14,
) -> pd.DataFrame:
    """Key Player 뉴스 피드 조회 (processing_pipeline='news_feed')."""
    cutoff = datetime.utcnow() - timedelta(days=days_back)
    q = session.query(MarketSignal).filter(
        MarketSignal.processing_pipeline == "news_feed",
        MarketSignal.published_at >= cutoff,
    )
    if company:
        q = q.filter(MarketSignal.category == company)
    rows = q.order_by(MarketSignal.published_at.desc()).limit(200).all()

    return pd.DataFrame([{
        "title": r.title,
        "source_url": r.source_url,
        "publisher": r.publisher,
        "category": r.category,
        "published_at": r.published_at,
        "confidence_score": r.confidence_score,
        "key_insights": r.key_insights or [],
    } for r in rows])


def upsert_signal(session: Session, signal_data: dict) -> tuple[bool, str]:
    """
    Idempotent upsert by event_id.
    Returns: (was_inserted, event_id)
    """
    event_id = signal_data.get("event_id")
    if not event_id:
        import uuid
        event_id = str(uuid.uuid4())
        signal_data["event_id"] = event_id

    existing = session.query(MarketSignal).filter_by(event_id=event_id).first()

    if existing:
        # Update mutable fields
        existing.summary = signal_data.get("summary", existing.summary)
        existing.strategic_implication = signal_data.get("strategic_implication", existing.strategic_implication)
        existing.key_insights = signal_data.get("key_insights", existing.key_insights)
        existing.updated_at = datetime.utcnow()
        return False, event_id
    else:
        new_signal = MarketSignal(**{
            k: v for k, v in signal_data.items()
            if hasattr(MarketSignal, k)
        })
        session.add(new_signal)
        return True, event_id