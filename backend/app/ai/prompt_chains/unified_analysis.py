"""
Single-Pass Unified Analysis Prompt Chain.

Consolidates Data Synthesis, Risk Quantification, Scenario Generation, 
and XAI Report into a single API call for massive speed and latency reduction.
The LLM performs Chain of Thought (CoT) reasoning internally and outputs a 
single composite JSON object.
"""
import json
from datetime import datetime, timezone
from typing import Any

from app.ai.base_provider import AIMessage, BaseAIProvider

SYSTEM_PROMPT = """You are PRAVAAH's Master Intelligence Engine — an elite hydrometeorological analyst for West Bengal flood assessment.

Your task is to analyze the provided raw district data and generate a comprehensive, multi-stage flood intelligence report in a SINGLE pass. You will perform internal Chain-of-Thought reasoning by sequentially generating a Risk Assessment, Scenario Projections, and finally an XAI Report.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no prose, no code fences.
2. The JSON must contain exactly three top-level keys: "risk_assessment", "scenarios", "xai_report".
3. All numeric scores (0.0-10.0) must be floats.
4. Probabilities in the scenarios must sum to 1.0.
5. In the XAI report, trace every claim back to the provided raw input data.
6. The entire output will be parsed programmatically. Any formatting deviation will cause pipeline failure.
"""

UNIFIED_PROMPT_TEMPLATE = """Generate a complete flood analysis for {district_name} district.

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

=== SCORING METHODOLOGY (For Risk Assessment) ===
- ATMOSPHERIC RISK (0-10): Based on forecast rainfall and storms.
- RIVER OVERFLOW RISK (0-10): Based on warning/danger level ratios.
- HISTORICAL VULNERABILITY (0-10): Based on past events.
- TOPOGRAPHICAL RISK (0-10): Based on elevation/base risk multiplier.
- SATURATION RISK (0-10): Based on 30-day rainfall vs normal.
- COMPOSITE INDEX FORMULA: (Atmospheric*0.25 + River*0.30 + Historical*0.15 + Topographical*0.10 + Saturation*0.20) * 10 * BaseMultiplier (0-100 scale).

=== REQUIRED OUTPUT JSON SCHEMA ===
{{
  "risk_assessment": {{
    "risk_dimensions": {{
      "atmospheric_risk": {{"score": <float 0-10>, "rationale": "<string>", "key_driver": "<string>"}},
      "river_overflow_risk": {{"score": <float 0-10>, "rationale": "<string>", "key_driver": "<string>"}},
      "historical_vulnerability": {{"score": <float 0-10>, "rationale": "<string>", "key_driver": "<string>"}},
      "topographical_risk": {{"score": <float 0-10>, "rationale": "<string>", "key_driver": "<string>"}},
      "saturation_risk": {{"score": <float 0-10>, "rationale": "<string>", "key_driver": "<string>"}}
    }},
    "confidence_score": <float 0.0-1.0>
  }},
  "scenarios": {{
    "scenarios": {{
      "best_case": {{
        "label": "Best Case",
        "probability": <float>,
        "trigger_conditions": ["<string>"],
        "72h_timeline": [{{"hours_from_now": 24, "description": "<string>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}],
        "projected_impact": {{"estimated_flood_area_km2": <float>, "estimated_affected_population": <int>, "infrastructure_risk": "<string>", "evacuation_required": <bool>}},
        "final_risk_score_estimate": <float>
      }},
      "most_likely": {{
        "label": "Most Likely",
        "probability": <float>,
        "trigger_conditions": ["<string>"],
        "72h_timeline": [{{"hours_from_now": 24, "description": "<string>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}],
        "projected_impact": {{"estimated_flood_area_km2": <float>, "estimated_affected_population": <int>, "infrastructure_risk": "<string>", "evacuation_required": <bool>}},
        "final_risk_score_estimate": <float>
      }},
      "worst_case": {{
        "label": "Worst Case",
        "probability": <float>,
        "trigger_conditions": ["<string>"],
        "72h_timeline": [{{"hours_from_now": 24, "description": "<string>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}],
        "projected_impact": {{"estimated_flood_area_km2": <float>, "estimated_affected_population": <int>, "infrastructure_risk": "<string>", "evacuation_required": <bool>}},
        "final_risk_score_estimate": <float>
      }}
    }}
  }},
  "xai_report": {{
    "deployment_priority_rank": <int 1-10>,
    "executive_summary": "<2-3 sentence summary>",
    "reasoning_chain": [
      {{"step": 1, "title": "<string>", "observation": "<cite values>", "implication": "<meaning>"}}
    ],
    "recommendations": [
      {{"priority": 1, "category": "<string>", "action": "<action>", "responsible_agency": "<agency>", "timeframe": "<hours>", "rationale": "<why>"}}
    ],
    "key_risk_indicators": {{
      "primary_threat": "<string>",
      "secondary_threat": "<string>",
      "converging_factors": ["<string>"],
      "most_likely_impact_zone": "<string>"
    }},
    "confidence_assessment": {{
      "overall_confidence": <float>,
      "data_completeness": "<string>",
      "uncertainty_sources": ["<string>"],
      "reliability_note": "<string>"
    }},
    "sms_alert_text": "<under 160 chars>"
  }}
}}"""


async def run_unified_analysis(
    ai_provider: BaseAIProvider,
    district_info: Any,
    weather_data: dict[str, Any],
    river_data: list[dict[str, Any]],
    historical_profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Executes the entire analytical CoT pipeline in a single LLM pass.
    """
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
        "major_rivers": district_info.major_rivers,
        "base_flood_risk": district_info.base_flood_risk,
    }

    prompt = UNIFIED_PROMPT_TEMPLATE.format(
        district_name=district_info.name,
        district_metadata=json.dumps(district_meta, indent=2),
        weather_data=json.dumps(weather_data.get("current_conditions", {}), indent=2),
        forecast_data=forecast_lines,
        historical_30day_mm=weather_data.get("historical_30day_rainfall_mm", 0.0),
        river_data=river_lines,
        historical_profile=json.dumps(historical_profile, indent=2),
    )

    messages = [
        AIMessage(role="system", content=SYSTEM_PROMPT),
        AIMessage(role="user", content=prompt),
    ]

    response = await ai_provider.chat(
        messages=messages,
        temperature=0.1,
        json_mode=True,
    )

    try:
        master_data = json.loads(response.content)
        return master_data
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Unified Analysis returned invalid JSON: {exc}\n"
            f"Raw (first 500 chars): {response.content[:500]}"
        ) from exc
