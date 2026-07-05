"""
River gauge data fetcher.

Loads river gauge station data from the curated static JSON file.
In a future production deployment, this fetcher can be extended to
scrape CWC's flood forecasting portal (ffs.india-water.gov.in) when
official API access is granted.

Provides:
  - All station readings for a district
  - Overflow risk assessment (current vs danger level ratio)
  - Trend classification (critical/warning/normal)
"""
import json
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings
from app.data_ingestion.base_fetcher import BaseFetcher, DataFetchError

settings = get_settings()


class RiverGaugeFetcher(BaseFetcher):
    """
    Fetches river gauge readings from the static JSON data file.

    Each station record includes current level, danger level, warning level,
    and discharge. This fetcher computes derived metrics:
      - overflow_risk_ratio: current_level / danger_level (0.0–1.0+)
      - status: "critical" | "warning" | "normal"
      - percent_to_danger: how close the level is to danger threshold
    """

    def __init__(self) -> None:
        self._stations_path = Path(settings.river_stations_path)
        self._all_stations: list[dict[str, Any]] | None = None

    def _load_stations(self) -> list[dict[str, Any]]:
        """Load and cache station data from the JSON file (lazy, once per instance)."""
        if self._all_stations is None:
            if not self._stations_path.exists():
                raise DataFetchError(
                    message=f"River stations file not found: {self._stations_path}",
                    source=self.source_name,
                )
            with open(self._stations_path, encoding="utf-8") as f:
                self._all_stations = json.load(f)
            logger.info(f"Loaded {len(self._all_stations)} river gauge stations.")
        return self._all_stations

    def _compute_derived_metrics(
        self, station: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Compute overflow risk ratio and status category for a station.

        overflow_risk_ratio: 0.0 = empty, 1.0 = at danger level, >1.0 = above danger
        """
        current = station["current_level_m"]
        danger = station["danger_level_m"]
        warning = station["warning_level_m"]
        normal = station["normal_level_m"]

        # Clamp to avoid division by zero
        range_normal_to_danger = max(danger - normal, 0.01)
        overflow_risk_ratio = (current - normal) / range_normal_to_danger
        overflow_risk_ratio = round(max(0.0, min(overflow_risk_ratio, 1.5)), 3)

        percent_to_danger = round(
            ((current - normal) / range_normal_to_danger) * 100, 1
        )

        if current >= danger:
            status = "critical"
        elif current >= warning:
            status = "warning"
        else:
            status = "normal"

        return {
            **station,
            "overflow_risk_ratio": overflow_risk_ratio,
            "percent_to_danger": percent_to_danger,
            "status": status,
        }

    async def fetch(self, district_id: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch river gauge data, optionally filtered by district.

        Args:
            district_id: If provided, return only stations for that district.
                         If None, return all stations.

        Returns:
            List of station dicts with derived overflow risk metrics.
        """
        try:
            stations = self._load_stations()

            if district_id:
                stations = [s for s in stations if s["district_id"] == district_id]

            enriched = [self._compute_derived_metrics(s) for s in stations]
            return enriched

        except DataFetchError:
            raise
        except Exception as exc:
            raise DataFetchError(
                message=f"Failed to process river gauge data: {exc}",
                source=self.source_name,
            ) from exc

    async def fetch_all_with_risk(self) -> dict[str, Any]:
        """
        Fetch all stations and compute district-level river overflow risk summary.

        Returns:
            Dict mapping district_id → max overflow risk ratio and critical station count.
        """
        all_stations = await self.fetch()
        district_risk: dict[str, dict[str, Any]] = {}

        for station in all_stations:
            district = station["district_id"]
            ratio = station["overflow_risk_ratio"]
            status = station["status"]

            if district not in district_risk:
                district_risk[district] = {
                    "max_overflow_risk": 0.0,
                    "critical_stations": 0,
                    "warning_stations": 0,
                    "stations": [],
                }

            district_risk[district]["stations"].append(station)
            district_risk[district]["max_overflow_risk"] = max(
                district_risk[district]["max_overflow_risk"], ratio
            )
            if status == "critical":
                district_risk[district]["critical_stations"] += 1
            elif status == "warning":
                district_risk[district]["warning_stations"] += 1

        return district_risk

    @property
    def source_name(self) -> str:
        return "River Gauge (Static + CWC)"

    @property
    def cache_key_prefix(self) -> str:
        return "river"
