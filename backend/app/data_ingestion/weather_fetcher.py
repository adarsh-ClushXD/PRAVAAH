"""
Weather data fetcher using the Open-Meteo API.

Open-Meteo is a free, open-source weather API with no API key required.
It provides hourly and daily forecast data at high spatial resolution
(1km–11km) for any coordinate worldwide.

API Documentation: https://open-meteo.com/en/docs

For each district, this fetcher retrieves:
  - 7-day daily forecast: precipitation sum, max/min temperature,
    wind speed, humidity, weather code
  - 24-hour hourly data: precipitation, temperature at 2m,
    relative humidity, wind speed
  - Historical 30-day rainfall total (from historical API)
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from loguru import logger

from app.data_ingestion.base_fetcher import BaseFetcher, DataFetchError
from app.geospatial.district_registry import DistrictInfo


class WeatherFetcher(BaseFetcher):
    """
    Fetches multi-day weather forecasts and historical rainfall data
    from the Open-Meteo API for a given district.
    """

    FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast"
    HISTORICAL_API_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self) -> None:
        self._timeout = httpx.Timeout(30.0)

    async def fetch(self, district: DistrictInfo) -> dict[str, Any]:
        """
        Fetch complete weather data for a district.

        Args:
            district: The DistrictInfo object with lat/lon coordinates.

        Returns:
            Normalized weather data dict with keys:
              - district_id, district_name
              - forecast_7day: list of daily forecast dicts
              - hourly_24h: list of hourly dicts for the next 24 hours
              - historical_30day_rainfall_mm: total rainfall over past 30 days
              - current_conditions: snapshot of latest conditions
              - fetched_at: ISO timestamp of fetch time
        """
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                forecast_data, historical_data = await self._fetch_parallel(
                    client, district
                )

            normalized = self._normalize(district, forecast_data, historical_data)
            logger.debug(f"Weather fetched for {district.name}: {normalized['current_conditions']}")
            return normalized

        except httpx.TimeoutException as exc:
            raise DataFetchError(
                message=f"Open-Meteo timeout for {district.name}: {exc}",
                source=self.source_name,
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise DataFetchError(
                message=f"Open-Meteo HTTP {exc.response.status_code} for {district.name}",
                source=self.source_name,
            ) from exc
        except KeyError as exc:
            raise DataFetchError(
                message=f"Unexpected Open-Meteo response format: missing key {exc}",
                source=self.source_name,
            ) from exc

    async def _fetch_parallel(
        self,
        client: httpx.AsyncClient,
        district: DistrictInfo,
    ) -> tuple[dict, dict]:
        """Fetch forecast and historical data concurrently."""
        import asyncio

        forecast_params = {
            "latitude": district.lat,
            "longitude": district.lon,
            "daily": [
                "precipitation_sum",
                "temperature_2m_max",
                "temperature_2m_min",
                "wind_speed_10m_max",
                "weathercode",
                "precipitation_probability_max",
            ],
            "hourly": [
                "precipitation",
                "temperature_2m",
                "relative_humidity_2m",
                "wind_speed_10m",
                "precipitation_probability",
            ],
            "timezone": "Asia/Kolkata",
            "forecast_days": 7,
        }

        today = datetime.now(timezone.utc).date()
        thirty_days_ago = today - timedelta(days=30)
        yesterday = today - timedelta(days=1)

        historical_params = {
            "latitude": district.lat,
            "longitude": district.lon,
            "start_date": thirty_days_ago.isoformat(),
            "end_date": yesterday.isoformat(),
            "daily": ["precipitation_sum"],
            "timezone": "Asia/Kolkata",
        }

        forecast_resp, historical_resp = await asyncio.gather(
            client.get(self.FORECAST_API_URL, params=forecast_params),
            client.get(self.HISTORICAL_API_URL, params=historical_params),
        )
        forecast_resp.raise_for_status()
        historical_resp.raise_for_status()

        return forecast_resp.json(), historical_resp.json()

    def _normalize(
        self,
        district: DistrictInfo,
        forecast: dict[str, Any],
        historical: dict[str, Any],
    ) -> dict[str, Any]:
        """Transform raw API responses into the normalized data structure."""
        daily = forecast["daily"]
        hourly = forecast["hourly"]

        # Build 7-day daily forecast
        forecast_7day = []
        for i, date_str in enumerate(daily["time"]):
            forecast_7day.append({
                "date": date_str,
                "precipitation_mm": daily["precipitation_sum"][i] or 0.0,
                "temp_max_c": daily["temperature_2m_max"][i] or 0.0,
                "temp_min_c": daily["temperature_2m_min"][i] or 0.0,
                "wind_speed_kmh": daily["wind_speed_10m_max"][i] or 0.0,
                "weather_code": daily["weathercode"][i] or 0,
                "precipitation_probability_pct": daily["precipitation_probability_max"][i] or 0,
            })

        # Build next 24 hourly records
        hourly_24h = []
        for i in range(min(24, len(hourly["time"]))):
            hourly_24h.append({
                "time": hourly["time"][i],
                "precipitation_mm": hourly["precipitation"][i] or 0.0,
                "temperature_c": hourly["temperature_2m"][i] or 0.0,
                "humidity_pct": hourly["relative_humidity_2m"][i] or 0,
                "wind_speed_kmh": hourly["wind_speed_10m"][i] or 0.0,
                "precipitation_probability_pct": hourly["precipitation_probability"][i] or 0,
            })

        # Historical 30-day total rainfall
        hist_daily = historical.get("daily", {})
        hist_precip = hist_daily.get("precipitation_sum", [])
        historical_30day_mm = sum(v for v in hist_precip if v is not None)

        # Current conditions (first hourly entry = now)
        current = hourly_24h[0] if hourly_24h else {}

        return {
            "district_id": district.id,
            "district_name": district.name,
            "lat": district.lat,
            "lon": district.lon,
            "forecast_7day": forecast_7day,
            "hourly_24h": hourly_24h,
            "historical_30day_rainfall_mm": round(historical_30day_mm, 1),
            "current_conditions": {
                "temperature_c": current.get("temperature_c", 0.0),
                "humidity_pct": current.get("humidity_pct", 0),
                "precipitation_mm": current.get("precipitation_mm", 0.0),
                "wind_speed_kmh": current.get("wind_speed_kmh", 0.0),
            },
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    @property
    def source_name(self) -> str:
        return "Open-Meteo"

    @property
    def cache_key_prefix(self) -> str:
        return "weather"
