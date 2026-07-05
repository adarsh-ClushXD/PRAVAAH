"""
CoT Step 1: Data Synthesis Prompt Chain.

Transforms raw multi-source data (weather, river, historical, topographical)
into a clean, structured fact sheet that subsequent reasoning steps consume.
This separation ensures Gemma doesn't mix data normalization with risk analysis.

The 31B model can handle complex structured input — we exploit the full
256K context window to provide comprehensive district data.
"""
import json
from typing import Any

from app.ai.base_provider import AIMessage, BaseAIProvider


SYSTEM_PROMPT = """You are PRAVAAH's Data Intelligence Module — a precision data analyst specializing in hydrometeorological risk assessment for West Bengal, India.

Your task is ONLY to synthesize and normalize the provided raw data into a clean structured fact sheet. Do NOT perform risk analysis or make predictions in this step.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no prose, no code fences.
2. Never invent or extrapolate data not present in the input.
3. If a data field is missing or null, represent it as null in the output.
4. All numeric values must be float or int — never strings.
5. Your output will be parsed by an automated system — formatting errors will cause pipeline failure.
"""

SYNTHESIS_PROMPT_TEMPLATE = """Synthesize the following raw multi-source data for {district_name} district into a structured fact sheet.

=== RAW INPUT DATA ===

--- DISTRICT METADATA ---
{district_metadata}

--- CURRENT WEATHER CONDITIONS ---
{weather_data}

--- 7-DAY RAINFALL FORECAST ---
{forecast_data}

--- HISTORICAL 30-DAY RAINFALL ---
Total rainfall over past 30 days: {historical_30day_mm} mm

--- RIVER GAUGE STATIONS IN/NEAR DISTRICT ---
{river_data}

--- HISTORICAL FLOOD PROFILE (2000-2024) ---
{historical_profile}

=== REQUIRED OUTPUT SCHEMA ===
Return exactly this JSON structure, all fields required:

{{
  "district_id": "<string>",
  "district_name": "<string>",
  "synthesis_timestamp": "<ISO datetime string>",
  "geographic_context": {{
    "latitude": <float>,
    "longitude": <float>,
    "elevation_m": <float>,
    "area_km2": <float>,
    "population_density": <int>,
    "major_rivers": ["<river names>"],
    "division": "<string>"
  }},
  "current_atmospheric_state": {{
    "temperature_c": <float>,
    "humidity_pct": <int>,
    "current_precipitation_mm": <float>,
    "wind_speed_kmh": <float>
  }},
  "rainfall_analysis": {{
    "total_forecast_7day_mm": <float>,
    "peak_daily_forecast_mm": <float>,
    "peak_forecast_date": "<YYYY-MM-DD>",
    "historical_30day_total_mm": <float>,
    "average_daily_rainfall_mm": <float>,
    "consecutive_high_rain_days": <int>
  }},
  "river_status_summary": {{
    "monitored_stations_count": <int>,
    "critical_stations_count": <int>,
    "warning_stations_count": <int>,
    "highest_overflow_risk_ratio": <float>,
    "most_critical_station": "<station name or null>",
    "most_critical_river": "<river name or null>"
  }},
  "historical_flood_profile": {{
    "total_recorded_events": <int>,
    "flood_frequency_score": <float>,
    "historical_risk_score": <float>,
    "total_recorded_deaths": <int>,
    "worst_event_year": <int or null>,
    "worst_event_severity": "<mild|moderate|severe|catastrophic or null>",
    "events_last_5_years": <int>
  }},
  "topographical_risk_factors": {{
    "base_flood_risk_multiplier": <float>,
    "proximity_to_major_rivers": <int>,
    "elevation_category": "<highland|midland|lowland|coastal>"
  }}
}}"""


async def run_data_synthesis(
    ai_provider: BaseAIProvider,
    district_info: Any,
    weather_data: dict[str, Any],
    river_data: list[dict[str, Any]],
    historical_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute CoT Step 1: Data Synthesis.

    Sends all raw district data to Gemma and receives a normalized
    fact sheet JSON that forms the input to Step 2.

    Args:
        ai_provider: The active BaseAIProvider implementation.
        district_info: DistrictInfo object from the registry.
        weather_data: Normalized weather dict from WeatherFetcher.
        river_data: List of station dicts from RiverGaugeFetcher.
        historical_profile: Historical risk profile dict.

    Returns:
        Parsed and validated fact sheet dict.

    Raises:
        ValueError: If Gemma returns invalid or malformed JSON.
    """
    from datetime import datetime, timezone

    # Format forecast summary (first 7 days)
    forecast_lines = "\n".join(
        f"  Day {i+1} ({f['date']}): {f['precipitation_mm']}mm rain, "
        f"{f['temp_max_c']}°C max, {f['precipitation_probability_pct']}% probability"
        for i, f in enumerate(weather_data.get("forecast_7day", []))
    )

    # Format river stations
    river_lines = "\n".join(
        f"  • {s['station_name']} ({s['river']}): Level {s['current_level_m']}m / "
        f"Danger {s['danger_level_m']}m | Status: {s['status'].upper()} | "
        f"Risk Ratio: {s['overflow_risk_ratio']}"
        for s in river_data
    ) if river_data else "  No monitoring stations in/near this district."

    district_meta = {
        "id": district_info.id,
        "name": district_info.name,
        "lat": district_info.lat,
        "lon": district_info.lon,
        "elevation_m": district_info.elevation_m,
        "area_km2": district_info.area_km2,
        "population_density": district_info.population_density,
        "division": district_info.division,
        "major_rivers": district_info.major_rivers,
        "base_flood_risk": district_info.base_flood_risk,
    }

    recent_events = historical_profile.get("recent_events", [])
    hist_summary = {
        "total_events": historical_profile.get("total_events", 0),
        "flood_frequency_score": historical_profile.get("flood_frequency_score", 0.0),
        "historical_risk_score": historical_profile.get("historical_risk_score", 0.0),
        "total_deaths": historical_profile.get("total_deaths", 0),
        "events_last_5_years": len([e for e in recent_events if e.get("year", 0) >= 2020]),
        "worst_event": historical_profile.get("worst_event"),
    }

    prompt = SYNTHESIS_PROMPT_TEMPLATE.format(
        district_name=district_info.name,
        district_metadata=json.dumps(district_meta, indent=2),
        weather_data=json.dumps(weather_data.get("current_conditions", {}), indent=2),
        forecast_data=forecast_lines,
        historical_30day_mm=weather_data.get("historical_30day_rainfall_mm", 0.0),
        river_data=river_lines,
        historical_profile=json.dumps(hist_summary, indent=2),
    )

    messages = [
        AIMessage(role="system", content=SYSTEM_PROMPT),
        AIMessage(role="user", content=prompt),
    ]

    response = await ai_provider.chat(
        messages=messages,
        temperature=0.05,
        json_mode=True,
    )

    try:
        fact_sheet = json.loads(response.content)
        # Inject synthesis timestamp if Gemma omitted it
        if not fact_sheet.get("synthesis_timestamp"):
            fact_sheet["synthesis_timestamp"] = datetime.now(timezone.utc).isoformat()
        return fact_sheet
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Data synthesis returned invalid JSON: {exc}\n"
            f"Raw response (first 500 chars): {response.content[:500]}"
        ) from exc
