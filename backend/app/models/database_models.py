"""
SQLAlchemy ORM database models for PRAVAAH.

All persistent data is stored in SQLite via these models:
  - FloodAnalysis: Complete AI analysis pipeline result per district
  - WeatherCache: Cached weather readings (supplemental to CacheManager)
  - RiverReading: Timestamped river gauge snapshots
  - AlertEvent: High-priority alert events for audit trail

Note: The CacheManager uses its own raw SQL cache_entries table.
These ORM models store domain data with full relational structure.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FloodAnalysis(Base):
    """
    Stores the complete output of one AI pipeline run for a district.

    Each run produces 4 intermediate outputs (fact_sheet, risk_assessment,
    scenarios, xai_report) stored as serialized JSON, plus extracted
    scalar metrics for efficient querying.
    """

    __tablename__ = "flood_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    district_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    district_name: Mapped[str] = mapped_column(String(128), nullable=False)

    # Scalar metrics for fast dashboard queries
    composite_flood_risk_index: Mapped[float] = mapped_column(Float, nullable=False)
    risk_category: Mapped[str] = mapped_column(String(32), nullable=False)
    alert_level: Mapped[str] = mapped_column(String(16), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    deployment_priority_rank: Mapped[int] = mapped_column(Integer, nullable=True)

    # AI pipeline outputs (JSON serialized)
    fact_sheet_json: Mapped[str] = mapped_column(Text, nullable=False)
    risk_assessment_json: Mapped[str] = mapped_column(Text, nullable=False)
    scenarios_json: Mapped[str] = mapped_column(Text, nullable=False)
    xai_report_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    ai_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    pipeline_duration_seconds: Mapped[float] = mapped_column(Float, nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def get_fact_sheet(self) -> dict:
        return json.loads(self.fact_sheet_json)

    def get_risk_assessment(self) -> dict:
        return json.loads(self.risk_assessment_json)

    def get_scenarios(self) -> dict:
        return json.loads(self.scenarios_json)

    def get_xai_report(self) -> dict:
        return json.loads(self.xai_report_json)

    def __repr__(self) -> str:
        return (
            f"FloodAnalysis(id={self.id}, district={self.district_id}, "
            f"risk={self.composite_flood_risk_index}, alert={self.alert_level})"
        )


class RiverReading(Base):
    """Timestamped snapshot of a single river gauge station reading."""

    __tablename__ = "river_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    district_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    river_name: Mapped[str] = mapped_column(String(64), nullable=False)
    current_level_m: Mapped[float] = mapped_column(Float, nullable=False)
    danger_level_m: Mapped[float] = mapped_column(Float, nullable=False)
    overflow_risk_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    trend: Mapped[str] = mapped_column(String(16), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AlertEvent(Base):
    """
    Audit trail for high-priority alert events.

    Created when a district crosses a risk threshold that triggers
    an alert escalation (e.g., moves from YELLOW to RED).
    """

    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    alert_level: Mapped[str] = mapped_column(String(16), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=True)
    sms_alert_text: Mapped[str] = mapped_column(String(200), nullable=True)
    analysis_id: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
