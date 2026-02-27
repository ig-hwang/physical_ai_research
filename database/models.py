"""
PASIS Database Models
SQLAlchemy ORM - mirrors data-archivist SKILL.md DDL spec
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Text, Float, DateTime, Boolean,
    JSON, Integer, CheckConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class MarketSignal(Base):
    """
    Primary signals table - 4 scopes: Market, Tech, Case, Policy
    Grain: 1 record per unique signal (article/paper/filing)
    """
    __tablename__ = "market_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))

    # Taxonomy
    scope = Column(
        String(20), nullable=False,
        comment="Market|Tech|Case|Policy"
    )
    category = Column(String(100), nullable=True)

    # Content
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)
    strategic_implication = Column(Text, nullable=True)
    key_insights = Column(JSON, nullable=True)  # list[str]

    # Source Metadata (required per CLAUDE.md)
    source_url = Column(Text, nullable=False)
    publisher = Column(String(200), nullable=True)
    published_at = Column(DateTime, nullable=False)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    confidence_score = Column(Float, nullable=True)

    # Lineage
    processing_pipeline = Column(
        String(100), default="scout->analysis->archivist"
    )
    processed_at = Column(DateTime, default=datetime.utcnow)
    schema_version = Column(String(10), default="v1.0")

    # Quality
    data_quality_score = Column(Float, nullable=True)
    validation_errors = Column(JSON, nullable=True)  # list[str]

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("scope IN ('Market', 'Tech', 'Case', 'Policy')", name="ck_scope"),
        CheckConstraint("confidence_score BETWEEN 0.0 AND 1.0", name="ck_confidence"),
        CheckConstraint("data_quality_score BETWEEN 0.0 AND 1.0", name="ck_quality"),
        Index("idx_published_at", "published_at"),
        Index("idx_scope", "scope"),
        Index("idx_category", "category"),
        Index("idx_event_id", "event_id"),
    )

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "scope": self.scope,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "strategic_implication": self.strategic_implication,
            "key_insights": self.key_insights or [],
            "source_metadata": {
                "url": self.source_url,
                "publisher": self.publisher,
                "published_at": self.published_at.isoformat() if self.published_at else None,
                "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
                "confidence_score": self.confidence_score,
            },
            "data_quality_score": self.data_quality_score,
        }


class WeeklyReport(Base):
    """
    Auto-generated weekly strategic brief
    Grain: 1 record per ISO week
    """
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    week_start = Column(DateTime, nullable=False)
    week_end = Column(DateTime, nullable=False)
    iso_week = Column(String(10), nullable=False)  # e.g. "2026-W08"

    # Counts
    total_signals = Column(Integer, default=0)
    market_signals = Column(Integer, default=0)
    tech_signals = Column(Integer, default=0)
    case_signals = Column(Integer, default=0)
    policy_signals = Column(Integer, default=0)

    # Generated content (HTML)
    executive_summary = Column(Text, nullable=True)
    market_section = Column(Text, nullable=True)
    tech_section = Column(Text, nullable=True)
    case_section = Column(Text, nullable=True)
    policy_section = Column(Text, nullable=True)
    lgu_implications = Column(Text, nullable=True)
    full_report_html = Column(Text, nullable=True)

    # Metadata
    avg_confidence_score = Column(Float, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_week_start", "week_start"),
        Index("idx_iso_week", "iso_week"),
    )


class MonthlyReport(Base):
    """
    Auto-generated monthly strategic brief (Bain style)
    Grain: 1 record per calendar month
    """
    __tablename__ = "monthly_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    month_key = Column(String(7), unique=True, nullable=False)  # e.g. "2026-02"
    month_start = Column(DateTime, nullable=False)
    month_end = Column(DateTime, nullable=False)

    # Counts
    total_signals = Column(Integer, default=0)
    market_signals = Column(Integer, default=0)
    tech_signals = Column(Integer, default=0)
    case_signals = Column(Integer, default=0)
    policy_signals = Column(Integer, default=0)

    # Generated content (HTML)
    full_report_html = Column(Text, nullable=True)

    # Metadata
    generated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(50), nullable=True)

    __table_args__ = (
        Index("idx_month_start", "month_start"),
        Index("idx_month_key", "month_key"),
    )