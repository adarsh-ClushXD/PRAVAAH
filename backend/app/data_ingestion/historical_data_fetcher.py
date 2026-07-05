"""
Historical flood data fetcher.

Loads and analyzes the curated West Bengal flood event dataset (2000-2024).
Computes district-level historical risk indicators:
  - flood_frequency_score: normalized flood occurrence rate
  - mean_severity_score: average severity across all events
  - total_deaths: cumulative fatalities
  - max_affected_population: peak population impact
  - recency_weight: recent events weighted more heavily (decay factor)
"""
import json
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings
from app.data_ingestion.base_fetcher import BaseFetcher, DataFetchError

settings = get_settings()

SEVERITY_SCORES: dict[str, float] = {
    "mild": 1.0,
    "moderate": 2.0,
    "severe": 3.0,
    "catastrophic": 4.0,
}


class HistoricalDataFetcher(BaseFetcher):
    """
    Loads and computes historical flood risk indicators from the
    curated WB flood event dataset.

    The recency-weighted algorithm gives more weight to recent events
    (decay factor 0.85 per year going back from 2024) to account for
    changing climate patterns and infrastructure improvements.
    """

    CURRENT_YEAR = 2024
    DECAY_FACTOR = 0.85

    def __init__(self) -> None:
        self._data_path = Path(settings.historical_data_path)
        self._raw_data: dict[str, Any] | None = None

    def _load_data(self) -> dict[str, Any]:
        """Load historical data from JSON file (lazy, once per instance)."""
        if self._raw_data is None:
            if not self._data_path.exists():
                raise DataFetchError(
                    message=f"Historical data file not found: {self._data_path}",
                    source=self.source_name,
                )
            with open(self._data_path, encoding="utf-8") as f:
                self._raw_data = json.load(f)
            logger.info(
                f"Loaded {len(self._raw_data['events'])} historical flood events."
            )
        return self._raw_data

    def _compute_recency_weight(self, event_year: int) -> float:
        """
        Compute the temporal recency weight for a flood event.

        Events from the most recent year have weight 1.0.
        Weight decays by DECAY_FACTOR for each year going back.
        """
        years_ago = max(0, self.CURRENT_YEAR - event_year)
        return self.DECAY_FACTOR ** years_ago

    async def fetch(
        self, district_id: str | None = None
    ) -> dict[str, Any]:
        """
        Fetch historical flood risk profile for one or all districts.

        Args:
            district_id: If provided, return analysis for that district only.
                         If None, return analysis for all districts.

        Returns:
            Dict mapping district_id → historical risk profile dict with keys:
              - total_events: total flood event count
              - flood_frequency_score: 0.0–10.0 normalized frequency
              - mean_severity_score: 0.0–4.0 weighted average severity
              - historical_risk_score: 0.0–10.0 composite risk indicator
              - total_deaths: cumulative recorded fatalities
              - max_affected_population: peak affected population
              - worst_event: details of the most severe event
              - events_by_decade: event count bucketed by decade
              - recent_events: last 5 flood events
        """
        try:
            data = self._load_data()
            events = data["events"]

            if district_id:
                events = [e for e in events if e["district_id"] == district_id]

            return self._compute_risk_profiles(events, district_id)

        except DataFetchError:
            raise
        except Exception as exc:
            raise DataFetchError(
                message=f"Failed to process historical data: {exc}",
                source=self.source_name,
            ) from exc

    def _compute_risk_profiles(
        self,
        events: list[dict[str, Any]],
        target_district: str | None,
    ) -> dict[str, Any]:
        """Compute per-district historical risk profiles from the event list."""
        district_events: dict[str, list[dict]] = {}

        for event in events:
            did = event["district_id"]
            district_events.setdefault(did, []).append(event)

        profiles: dict[str, Any] = {}

        for district, d_events in district_events.items():
            total_events = len(d_events)
            total_years = self.CURRENT_YEAR - 2000 + 1

            # Recency-weighted severity sum
            weighted_severity_sum = sum(
                SEVERITY_SCORES.get(e["severity"], 1.0)
                * self._compute_recency_weight(e["year"])
                for e in d_events
            )
            max_possible_weighted = (
                SEVERITY_SCORES["catastrophic"]
                * sum(self._compute_recency_weight(y) for y in range(2000, self.CURRENT_YEAR + 1))
            )

            # Flood frequency: events per year, normalized to 0-10
            frequency_per_year = total_events / total_years
            flood_frequency_score = min(frequency_per_year * 10, 10.0)

            # Severity score: weighted average, normalized to 0-10
            mean_severity_raw = (
                weighted_severity_sum / total_events if total_events > 0 else 0.0
            )
            mean_severity_score = round(mean_severity_raw, 2)

            # Composite historical risk (0-10)
            historical_risk_score = round(
                (flood_frequency_score * 0.4 + mean_severity_score * (10 / 4) * 0.6),
                2,
            )
            historical_risk_score = min(historical_risk_score, 10.0)

            # Aggregate statistics
            total_deaths = sum(e["deaths"] for e in d_events)
            max_affected = max((e["affected_population"] for e in d_events), default=0)

            # Worst event
            worst_event = max(
                d_events,
                key=lambda e: SEVERITY_SCORES.get(e["severity"], 0) * e["deaths"],
                default={},
            )

            # Events by decade
            events_by_decade: dict[str, int] = {
                "2000-2009": sum(1 for e in d_events if 2000 <= e["year"] <= 2009),
                "2010-2019": sum(1 for e in d_events if 2010 <= e["year"] <= 2019),
                "2020-2024": sum(1 for e in d_events if 2020 <= e["year"] <= 2024),
            }

            # 5 most recent events
            recent_events = sorted(d_events, key=lambda e: e["year"], reverse=True)[:5]

            profiles[district] = {
                "district_id": district,
                "total_events": total_events,
                "flood_frequency_score": round(flood_frequency_score, 2),
                "mean_severity_score": mean_severity_score,
                "historical_risk_score": historical_risk_score,
                "total_deaths": total_deaths,
                "max_affected_population": max_affected,
                "worst_event": worst_event,
                "events_by_decade": events_by_decade,
                "recent_events": recent_events,
            }

        # If filtering by district and no events found, return empty profile
        if target_district and target_district not in profiles:
            profiles[target_district] = {
                "district_id": target_district,
                "total_events": 0,
                "flood_frequency_score": 0.0,
                "mean_severity_score": 0.0,
                "historical_risk_score": 0.0,
                "total_deaths": 0,
                "max_affected_population": 0,
                "worst_event": None,
                "events_by_decade": {"2000-2009": 0, "2010-2019": 0, "2020-2024": 0},
                "recent_events": [],
            }

        return profiles

    @property
    def source_name(self) -> str:
        return "Historical Flood Records (NDMA/IMD 2000-2024)"

    @property
    def cache_key_prefix(self) -> str:
        return "historical"
