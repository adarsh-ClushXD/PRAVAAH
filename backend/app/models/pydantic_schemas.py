"""
Pydantic request/response schemas for all PRAVAAH API endpoints.

All API responses are typed and validated through these schemas.
They serve as the contract between the backend and frontend,
and as living documentation in the OpenAPI spec.
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Common ─────────────────────────────────────────────────────────────────────

class RiskDimension(BaseModel):
    score: float = Field(ge=0.0, le=10.0)
    rationale: str
    key_driver: str


class RiskDimensions(BaseModel):
    atmospheric_risk: RiskDimension
    river_overflow_risk: RiskDimension
    historical_vulnerability: RiskDimension
    topographical_risk: RiskDimension
    saturation_risk: RiskDimension


# ── District Schemas ───────────────────────────────────────────────────────────

class DistrictSummary(BaseModel):
    """Lightweight district summary for the dashboard risk matrix."""
    district_id: str
    district_name: str
    lat: float
    lon: float
    composite_flood_risk_index: float | None = None
    risk_category: str | None = None
    alert_level: str | None = None
    confidence_score: float | None = None
    primary_threat: str | None = None
    last_analyzed_at: datetime | None = None
    major_rivers: list[str] = []
    base_flood_risk: float


class DistrictDetail(BaseModel):
    """Full district detail including latest analysis."""
    district_id: str
    district_name: str
    lat: float
    lon: float
    elevation_m: float
    area_km2: float
    population_density: int
    division: str
    major_rivers: list[str]
    base_flood_risk: float
    latest_analysis: "AnalysisResponse | None" = None


# ── Weather Schemas ────────────────────────────────────────────────────────────

class DailyForecast(BaseModel):
    date: str
    precipitation_mm: float
    temp_max_c: float
    temp_min_c: float
    wind_speed_kmh: float
    weather_code: int
    precipitation_probability_pct: int


class CurrentConditions(BaseModel):
    temperature_c: float
    humidity_pct: int
    precipitation_mm: float
    wind_speed_kmh: float


class WeatherResponse(BaseModel):
    district_id: str
    district_name: str
    current_conditions: CurrentConditions
    forecast_7day: list[DailyForecast]
    historical_30day_rainfall_mm: float
    fetched_at: str


# ── River Schemas ─────────────────────────────────────────────────────────────

class RiverStationResponse(BaseModel):
    station_id: str
    station_name: str
    district_id: str
    river: str
    lat: float
    lon: float
    current_level_m: float
    danger_level_m: float
    warning_level_m: float
    normal_level_m: float
    overflow_risk_ratio: float
    percent_to_danger: float
    status: str
    trend: str
    discharge_cumecs: float
    last_updated: str


class DistrictRiverSummary(BaseModel):
    district_id: str
    max_overflow_risk: float
    critical_stations: int
    warning_stations: int
    stations: list[RiverStationResponse]


# ── Analysis Schemas ──────────────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    """Request body to trigger a new AI analysis for a district."""
    district_id: str
    force_refresh: bool = Field(
        default=False,
        description="If True, bypass cache and run fresh analysis.",
    )


class ReasoningStep(BaseModel):
    step: int
    title: str
    observation: str
    implication: str


class Recommendation(BaseModel):
    priority: int
    category: str
    action: str
    responsible_agency: str
    timeframe: str
    rationale: str


class ScenarioProjection(BaseModel):
    label: str
    probability: float
    trigger_conditions: list[str]
    projected_impact: dict[str, Any]
    final_risk_score_estimate: float


class AnalysisResponse(BaseModel):
    """Complete analysis pipeline result returned to the frontend."""
    analysis_id: str
    district_id: str
    district_name: str
    created_at: datetime

    # Core metrics
    composite_flood_risk_index: float
    risk_category: str
    alert_level: str
    confidence_score: float
    deployment_priority_rank: int | None = None

    # XAI content
    executive_summary: str
    reasoning_chain: list[ReasoningStep]
    recommendations: list[Recommendation]
    sms_alert_text: str | None = None

    # Risk dimensions
    risk_dimensions: RiskDimensions | None = None

    # Scenarios
    scenarios: dict[str, ScenarioProjection] | None = None

    # Key indicators
    key_risk_indicators: dict[str, Any] | None = None
    confidence_assessment: dict[str, Any] | None = None

    # Pipeline metadata
    ai_provider: str
    model_name: str
    total_tokens_used: int
    pipeline_duration_seconds: float | None = None


class AnalysisTriggerResponse(BaseModel):
    """Response when a new analysis is queued or completed."""
    status: str
    message: str
    analysis_id: str | None = None
    district_id: str


# ── Report Schemas ────────────────────────────────────────────────────────────

class ReportMetadata(BaseModel):
    analysis_id: str
    district_id: str
    district_name: str
    generated_at: datetime
    format: str


# ── Health Schema ─────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
    ai_provider: str
    ai_provider_healthy: bool
