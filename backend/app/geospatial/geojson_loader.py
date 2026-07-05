"""
GeoJSON loader for West Bengal district boundaries.

Loads the WB district GeoJSON file and provides methods to:
  - Return the raw FeatureCollection for API responses
  - Inject risk scores into the GeoJSON properties for map rendering
  - Return a single district's Feature with enriched properties
"""
import json
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import get_settings

settings = get_settings()


class GeoJSONLoader:
    """
    Loads and enriches the West Bengal district GeoJSON boundaries.

    The GeoJSON file is loaded once at startup (lazy singleton) and
    cached in memory. Risk data is injected into feature properties
    at query time — the base GeoJSON is never mutated.
    """

    _geojson_data: dict[str, Any] | None = None

    @classmethod
    def _load(cls) -> dict[str, Any]:
        """Load GeoJSON from disk if not already in memory."""
        if cls._geojson_data is None:
            path = Path(settings.geojson_path)
            if not path.exists():
                logger.warning(
                    f"GeoJSON file not found at {path}. "
                    "Map will render without district boundaries."
                )
                cls._geojson_data = {"type": "FeatureCollection", "features": []}
            else:
                with open(path, encoding="utf-8") as f:
                    cls._geojson_data = json.load(f)
                logger.info(
                    f"Loaded GeoJSON with "
                    f"{len(cls._geojson_data.get('features', []))} features."
                )
        return cls._geojson_data

    @classmethod
    def get_feature_collection(cls) -> dict[str, Any]:
        """Return the raw GeoJSON FeatureCollection."""
        return cls._load()

    @classmethod
    def get_enriched_feature_collection(
        cls, risk_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Return the GeoJSON FeatureCollection with risk scores injected
        into each feature's properties.

        Args:
            risk_data: Dict mapping district_id → risk metrics dict.
                       Keys expected: composite_flood_risk_index, risk_category,
                       alert_level, confidence_score.

        Returns:
            A new FeatureCollection dict with enriched properties.
        """
        base = cls._load()
        enriched_features = []

        for feature in base.get("features", []):
            props = dict(feature.get("properties", {}))
            district_id = props.get("district_id") or props.get("ID_2") or props.get("NAME_2", "").lower().replace(" ", "_")

            if district_id in risk_data:
                risk = risk_data[district_id]
                props.update({
                    "composite_flood_risk_index": risk.get("composite_flood_risk_index"),
                    "risk_category": risk.get("risk_category"),
                    "alert_level": risk.get("alert_level"),
                    "confidence_score": risk.get("confidence_score"),
                    "primary_threat": risk.get("primary_threat"),
                })

            enriched_features.append({
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": props,
            })

        return {
            "type": "FeatureCollection",
            "features": enriched_features,
        }
