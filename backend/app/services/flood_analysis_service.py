"""
Flood Analysis Orchestration Service.

The central service that coordinates the entire AI pipeline:
  1. Gather data from all fetchers (with cache)
  2. Run 4-step CoT prompt chain through Gemma
  3. Persist results to database
  4. Return the complete analysis response

This service is the ONLY component that calls the AI pipeline.
All route handlers call this service — never the prompt chains directly.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider_factory import get_ai_provider
from app.ai.prompt_chains.unified_analysis import run_unified_analysis
from app.config import get_settings
from app.data_ingestion.cache_manager import CacheManager
from app.data_ingestion.historical_data_fetcher import HistoricalDataFetcher
from app.data_ingestion.river_gauge_fetcher import RiverGaugeFetcher
from app.data_ingestion.weather_fetcher import WeatherFetcher
from app.geospatial.district_registry import DistrictRegistry
from app.models.database_models import AlertEvent, FloodAnalysis
from app.models.pydantic_schemas import AnalysisResponse, ReasoningStep, Recommendation

settings = get_settings()

import json
import hashlib
import asyncio

_district_data_hashes = {}

class FloodAnalysisService:
    """
    Orchestrates the complete PRAVAAH AI analysis pipeline.

    Responsibilities:
      - Data aggregation with TTL caching
      - Sequential AI pipeline execution (4 CoT steps)
      - Result persistence and alert event generation
      - Response schema construction
    """

    def __init__(self) -> None:
        self._weather_fetcher = WeatherFetcher()
        self._river_fetcher = RiverGaugeFetcher()
        self._historical_fetcher = HistoricalDataFetcher()
        self._cache = CacheManager()
        self._ai_provider = get_ai_provider()

    async def run_analysis(
        self,
        district_id: str,
        db: AsyncSession,
        force_refresh: bool = False,
    ) -> AnalysisResponse:
        """
        Execute the full analysis pipeline for a district.

        Args:
            district_id: The district to analyze.
            db: Async SQLAlchemy session.
            force_refresh: If True, bypass all caches.

        Returns:
            Complete AnalysisResponse ready for API serialization.

        Raises:
            KeyError: If district_id is not in the registry.
            ValueError: If any pipeline step returns invalid data.
        """
        pipeline_start = time.perf_counter()
        district = DistrictRegistry.get_district(district_id)
        analysis_id = f"analysis_{district_id}_{uuid.uuid4().hex[:8]}"

        logger.info(
            f"Starting analysis pipeline for {district.name} "
            f"[{analysis_id}] | Provider: {self._ai_provider.provider_name}"
        )

        # ── Step 0: Gather Data ──────────────────────────────────────────────
        weather_data = await self._get_weather_data(district, force_refresh)
        river_data = await self._get_river_data(district_id, force_refresh)
        historical_profile = await self._get_historical_data(district_id, force_refresh)

        # ── DELTA CHECK OPTIMIZATION ─────────────────────────────────────────
        payload = json.dumps({"w": weather_data, "r": river_data}, sort_keys=True)
        payload_hash = hashlib.md5(payload.encode()).hexdigest()
        last_hash = _district_data_hashes.get(district_id)

        if not force_refresh and last_hash == payload_hash:
            logger.info(f"[{analysis_id}] Data unchanged for {district.name}. Skipping LLM pipeline.")
            cached = await self.get_latest_analysis(district_id, db)
            if cached:
                return cached
        
        # If changed, run the full pipeline
        logger.info(f"[{analysis_id}] Data gathered and changed. Starting AI pipeline...")

        # ── Step 1: Deterministic Fact Sheet Generation ───────────────────────
        logger.info(f"[{analysis_id}] Generating Fact Sheet (Deterministic)")
        fact_sheet = self._build_fact_sheet(district, weather_data, river_data, historical_profile)
        
        # ── Step 2: Unified Analysis LLM Call ─────────────────────────────────
        logger.info(f"[{analysis_id}] Executing Unified LLM Pipeline")
        master_data = await run_unified_analysis(
            ai_provider=self._ai_provider,
            district_info=district,
            weather_data=weather_data,
            river_data=river_data,
            historical_profile=historical_profile,
        )
        
        # ── Step 3: Unpack & Compute Math ────────────────────────────────────
        risk_assessment = master_data.get("risk_assessment", {})
        scenarios = master_data.get("scenarios", {})
        xai_report = master_data.get("xai_report", {})

        # Compute composite risk mathematically in Python for accuracy and speed
        risk_dims = risk_assessment.get("risk_dimensions", {})
        atm = float(risk_dims.get("atmospheric_risk", {}).get("score", 0.0))
        riv = float(risk_dims.get("river_overflow_risk", {}).get("score", 0.0))
        hst = float(risk_dims.get("historical_vulnerability", {}).get("score", 0.0))
        top = float(risk_dims.get("topographical_risk", {}).get("score", 0.0))
        sat = float(risk_dims.get("saturation_risk", {}).get("score", 0.0))
        
        base_mult = district.base_flood_risk
        raw_composite = (atm*0.25 + riv*0.30 + hst*0.15 + top*0.10 + sat*0.20) * 10 * min(base_mult, 1.5)
        composite = round(max(0.0, min(raw_composite, 100.0)), 1)
        
        # Determine category and alert
        if composite < 20:
            category, alert = "LOW", "GREEN"
        elif composite < 40:
            category, alert = "MODERATE", "YELLOW"
        elif composite < 60:
            category, alert = "HIGH", "ORANGE"
        elif composite < 80:
            category, alert = "VERY HIGH", "RED"
        else:
            category, alert = "CRITICAL", "PURPLE"

        # Inject computed values into the response payloads
        risk_assessment["composite_flood_risk_index"] = composite
        risk_assessment["risk_category"] = category
        xai_report["composite_flood_risk_index"] = composite
        xai_report["risk_category"] = category
        xai_report["alert_level"] = alert
        if "confidence_score" not in xai_report:
            xai_report["confidence_score"] = risk_assessment.get("confidence_score", 0.7)

        pipeline_duration = time.perf_counter() - pipeline_start
        logger.info(
            f"[{analysis_id}] Pipeline complete in {pipeline_duration:.1f}s | "
            f"Alert: {xai_report['alert_level']}"
        )
        
        # Update hash cache
        _district_data_hashes[district_id] = payload_hash

        # ── Persist to Database ───────────────────────────────────────────────
        analysis_record = await self._persist_analysis(
            db=db,
            analysis_id=analysis_id,
            district_id=district_id,
            district_name=district.name,
            xai_report=xai_report,
            risk_assessment=risk_assessment,
            fact_sheet=fact_sheet,
            scenarios=scenarios,
            pipeline_duration=pipeline_duration,
        )

        # ── Build and Return Response ─────────────────────────────────────────
        return self._build_response(
            analysis_id=analysis_id,
            district_id=district_id,
            district_name=district.name,
            xai_report=xai_report,
            risk_assessment=risk_assessment,
            scenarios=scenarios,
            pipeline_duration=pipeline_duration,
            created_at=analysis_record.created_at,
        )

    async def get_latest_analysis(
        self, district_id: str, db: AsyncSession
    ) -> AnalysisResponse | None:
        """
        Retrieve the most recent analysis for a district from the database.

        Returns None if no analysis has been run for this district yet.
        """
        result = await db.execute(
            select(FloodAnalysis)
            .where(
                FloodAnalysis.district_id == district_id,
                FloodAnalysis.is_latest == True,  # noqa: E712
            )
            .order_by(FloodAnalysis.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()

        if record is None:
            return None

        xai_report = record.get_xai_report()
        risk_assessment = record.get_risk_assessment()
        scenarios = record.get_scenarios()

        return self._build_response(
            analysis_id=record.analysis_id,
            district_id=record.district_id,
            district_name=record.district_name,
            xai_report=xai_report,
            risk_assessment=risk_assessment,
            scenarios=scenarios,
            pipeline_duration=record.pipeline_duration_seconds,
            created_at=record.created_at,
        )

    def _build_fact_sheet(
        self,
        district: Any,
        weather_data: dict,
        river_data: list,
        historical_profile: dict,
    ) -> dict:
        """Deterministically builds the fact sheet payload without using LLM."""
        
        # Calculate rainfall metrics
        forecast_7day = weather_data.get("forecast_7day", [])
        total_forecast_7day = sum(f.get("precipitation_mm", 0) for f in forecast_7day)
        
        # Calculate river metrics
        monitored_stations = len(river_data)
        critical_stations = sum(1 for r in river_data if r.get("overflow_risk_ratio", 0) >= 1.0)
        highest_ratio = max([r.get("overflow_risk_ratio", 0.0) for r in river_data] + [0.0])
        
        return {
            "district_id": district.id,
            "district_name": district.name,
            "geographic_context": {
                "latitude": district.lat,
                "longitude": district.lon,
                "elevation_m": district.elevation_m,
                "major_rivers": district.major_rivers,
            },
            "current_atmospheric_state": {
                "temperature_c": weather_data.get("current_conditions", {}).get("temperature_c", 0.0),
                "current_precipitation_mm": weather_data.get("current_conditions", {}).get("precipitation_mm", 0.0),
            },
            "rainfall_analysis": {
                "total_forecast_7day_mm": total_forecast_7day,
                "historical_30day_total_mm": weather_data.get("historical_30day_rainfall_mm", 0.0),
            },
            "river_status_summary": {
                "monitored_stations_count": monitored_stations,
                "critical_stations_count": critical_stations,
                "highest_overflow_risk_ratio": highest_ratio,
            },
            "historical_flood_profile": {
                "historical_risk_score": historical_profile.get("historical_risk_score", 0.0),
                "worst_event_severity": historical_profile.get("worst_event_severity", "None"),
            },
            "topographical_risk_factors": {
                "base_flood_risk_multiplier": district.base_flood_risk,
                "elevation_category": "midland" if district.elevation_m > 10 else "lowland",
            }
        }

    async def _get_weather_data(self, district: Any, force_refresh: bool) -> dict:
        """Get weather data with TTL cache."""
        if not force_refresh:
            cached = await self._cache.get("weather", district.id)
            if cached:
                return cached

        data = await self._weather_fetcher.fetch(district)
        await self._cache.set(
            "weather", district.id, data, settings.weather_cache_ttl_seconds
        )
        return data

    async def _get_river_data(self, district_id: str, force_refresh: bool) -> list:
        """Get river gauge data with TTL cache."""
        if not force_refresh:
            cached = await self._cache.get("river", district_id)
            if cached:
                return cached

        data = await self._river_fetcher.fetch(district_id)
        await self._cache.set(
            "river", district_id, data, settings.river_cache_ttl_seconds
        )
        return data

    async def _get_historical_data(self, district_id: str, force_refresh: bool) -> dict:
        """Get historical flood profile with TTL cache."""
        if not force_refresh:
            cached = await self._cache.get("historical", district_id)
            if cached:
                return cached

        all_profiles = await self._historical_fetcher.fetch(district_id)
        profile = all_profiles.get(district_id, {})
        await self._cache.set(
            "historical", district_id, profile, settings.historical_cache_ttl_seconds
        )
        return profile

    async def _persist_analysis(
        self,
        db: AsyncSession,
        analysis_id: str,
        district_id: str,
        district_name: str,
        xai_report: dict,
        risk_assessment: dict,
        fact_sheet: dict,
        scenarios: dict,
        pipeline_duration: float,
    ) -> FloodAnalysis:
        """
        Persist analysis result to the database.

        Marks previous analyses for this district as not-latest before
        inserting the new record.
        """
        # Mark previous analyses as not latest
        await db.execute(
            update(FloodAnalysis)
            .where(FloodAnalysis.district_id == district_id)
            .values(is_latest=False)
        )

        # Create alert event if HIGH or above
        alert_level = xai_report.get("alert_level", "YELLOW")
        if alert_level in ("ORANGE", "RED", "PURPLE"):
            alert = AlertEvent(
                district_id=district_id,
                alert_level=alert_level,
                risk_score=risk_assessment.get("composite_flood_risk_index", 0.0),
                trigger_reason=risk_assessment.get("primary_risk_driver", ""),
                sms_alert_text=xai_report.get("sms_alert_text", ""),
                analysis_id=analysis_id,
            )
            db.add(alert)

        # Insert new analysis record
        record = FloodAnalysis(
            analysis_id=analysis_id,
            district_id=district_id,
            district_name=district_name,
            composite_flood_risk_index=risk_assessment.get("composite_flood_risk_index", 0.0),
            risk_category=risk_assessment.get("risk_category", "MODERATE"),
            alert_level=xai_report.get("alert_level", "YELLOW"),
            confidence_score=xai_report.get("confidence_score", 0.7),
            deployment_priority_rank=xai_report.get("deployment_priority_rank"),
            fact_sheet_json=json.dumps(fact_sheet),
            risk_assessment_json=json.dumps(risk_assessment),
            scenarios_json=json.dumps(scenarios),
            xai_report_json=json.dumps(xai_report),
            ai_provider=self._ai_provider.provider_name,
            model_name=self._ai_provider.model_name,
            total_tokens_used=0,
            pipeline_duration_seconds=round(pipeline_duration, 2),
            is_latest=True,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    def _build_response(
        self,
        analysis_id: str,
        district_id: str,
        district_name: str,
        xai_report: dict,
        risk_assessment: dict,
        scenarios: dict,
        pipeline_duration: float | None,
        created_at: datetime,
    ) -> AnalysisResponse:
        """Construct an AnalysisResponse from pipeline outputs."""
        from app.models.pydantic_schemas import RiskDimension, RiskDimensions

        risk_dims_raw = risk_assessment.get("risk_dimensions", {})

        def parse_dim(key: str) -> RiskDimension:
            d = risk_dims_raw.get(key, {})
            return RiskDimension(
                score=float(d.get("score", 0.0)),
                rationale=d.get("rationale", ""),
                key_driver=d.get("key_driver", ""),
            )

        risk_dimensions = RiskDimensions(
            atmospheric_risk=parse_dim("atmospheric_risk"),
            river_overflow_risk=parse_dim("river_overflow_risk"),
            historical_vulnerability=parse_dim("historical_vulnerability"),
            topographical_risk=parse_dim("topographical_risk"),
            saturation_risk=parse_dim("saturation_risk"),
        ) if risk_dims_raw else None

        reasoning_chain = [
            ReasoningStep(**step)
            for step in xai_report.get("reasoning_chain", [])
            if isinstance(step, dict) and "step" in step
        ]

        recommendations = [
            Recommendation(**rec)
            for rec in xai_report.get("recommendations", [])
            if isinstance(rec, dict) and "priority" in rec
        ]

        scenario_data = scenarios.get("scenarios", {})
        from app.models.pydantic_schemas import ScenarioProjection
        parsed_scenarios = {}
        for key in ["best_case", "most_likely", "worst_case"]:
            sc = scenario_data.get(key, {})
            if sc:
                try:
                    parsed_scenarios[key] = ScenarioProjection(
                        label=sc.get("label", key),
                        probability=float(sc.get("probability", 0.33)),
                        trigger_conditions=sc.get("trigger_conditions", []),
                        projected_impact=sc.get("projected_impact", {}),
                        final_risk_score_estimate=float(sc.get("final_risk_score_estimate", 0.0)),
                    )
                except Exception:
                    pass

        return AnalysisResponse(
            analysis_id=analysis_id,
            district_id=district_id,
            district_name=district_name,
            created_at=created_at,
            composite_flood_risk_index=risk_assessment.get("composite_flood_risk_index", 0.0),
            risk_category=risk_assessment.get("risk_category", "MODERATE"),
            alert_level=xai_report.get("alert_level", "YELLOW"),
            confidence_score=float(xai_report.get("confidence_score", 0.7)),
            deployment_priority_rank=xai_report.get("deployment_priority_rank"),
            executive_summary=xai_report.get("executive_summary", ""),
            reasoning_chain=reasoning_chain,
            recommendations=recommendations,
            sms_alert_text=xai_report.get("sms_alert_text"),
            risk_dimensions=risk_dimensions,
            scenarios=parsed_scenarios if parsed_scenarios else None,
            key_risk_indicators=xai_report.get("key_risk_indicators"),
            confidence_assessment=xai_report.get("confidence_assessment"),
            ai_provider=self._ai_provider.provider_name,
            model_name=self._ai_provider.model_name,
            total_tokens_used=0,
            pipeline_duration_seconds=pipeline_duration,
        )
