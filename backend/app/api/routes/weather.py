"""Weather API routes."""
from fastapi import APIRouter, HTTPException

from app.data_ingestion.cache_manager import CacheManager
from app.data_ingestion.weather_fetcher import WeatherFetcher, DataFetchError
from app.geospatial.district_registry import DistrictRegistry
from app.models.pydantic_schemas import WeatherResponse
from app.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/weather/{district_id}", response_model=WeatherResponse)
async def get_district_weather(district_id: str) -> WeatherResponse:
    """
    Return 7-day weather forecast and current conditions for a district.
    Results are cached for 1 hour.
    """
    try:
        district = DistrictRegistry.get_district(district_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"District '{district_id}' not found.")

    cache = CacheManager()
    cached = await cache.get("weather", district_id)

    if cached:
        return WeatherResponse(**cached)

    fetcher = WeatherFetcher()
    try:
        data = await fetcher.fetch(district)
        await cache.set("weather", district_id, data, settings.weather_cache_ttl_seconds)
        return WeatherResponse(**data)
    except DataFetchError as exc:
        raise HTTPException(status_code=503, detail=f"Weather data unavailable: {exc.message}")
