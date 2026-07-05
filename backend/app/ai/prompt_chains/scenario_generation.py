"""
CoT Step 3: Scenario Generation Prompt Chain.

Using the risk quantification from Step 2, Gemma generates three distinct
future scenarios that represent the plausible range of outcomes over the
next 72 hours based on forecast uncertainty.

Scenario design:
  - BEST CASE: Favorable meteorological changes (rain decreases, rivers recede)
  - MOST LIKELY: Conditions evolve as currently forecast (baseline trajectory)
  - WORST CASE: Adverse compounding factors (more rain, dam releases, surge)

Each scenario includes a 72-hour timeline, specific trigger conditions,
projected impact metrics, and the probability Gemma assigns to it.
"""
import json
from typing import Any

from app.ai.base_provider import AIMessage, BaseAIProvider


SYSTEM_PROMPT = """You are PRAVAAH's Scenario Planning Engine — a hydrometeorological forecasting specialist for West Bengal disaster management.

Your task is to generate THREE DISTINCT future scenarios based on the current risk assessment. Each scenario must be internally consistent and grounded in the provided data.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no prose, no code fences.
2. All three scenario probabilities must sum to exactly 1.0.
3. Scenarios must represent genuinely different outcomes — not variations of the same outcome.
4. All projected metrics must be physically plausible (no river level dropping 10m in 12 hours).
5. Each scenario must include specific trigger conditions that would cause it to occur.
6. Impact estimates must scale proportionally to the risk score and affected area.
"""

SCENARIO_TEMPLATE = """Generate three future scenarios for {district_name} district over the next 72 hours.

=== RISK ASSESSMENT (Step 2 Output) ===
{risk_assessment}

=== DISTRICT CONTEXT ===
{district_context}

=== SCENARIO GENERATION GUIDELINES ===

BEST CASE SCENARIO:
- Rainfall reduces to ≤30% of forecast
- Rivers trending down or stable
- No additional dam releases
- External weather system dissipates
- Probability: typically 15-30% (lower if conditions are already severe)

MOST LIKELY SCENARIO:
- Conditions evolve as currently forecast (baseline)
- Rivers follow projected discharge curves
- Dam releases follow announced schedule
- No surprise weather events
- Probability: typically 45-65%

WORST CASE SCENARIO:
- Rainfall exceeds forecast by 40-80%
- Additional dam discharge (unplanned DVC release)
- One or more river embankment breaches
- Compound cyclonic/tidal effects if applicable
- Probability: typically 15-35% (higher if historical catastrophic events common)

=== REQUIRED OUTPUT SCHEMA ===
{{
  "district_id": "<string>",
  "district_name": "<string>",
  "scenario_generated_at": "<ISO datetime>",
  "forecast_horizon_hours": 72,
  "scenarios": {{
    "best_case": {{
      "label": "Best Case",
      "probability": <float 0.0-1.0>,
      "trigger_conditions": ["<specific meteorological/hydrological triggers>"],
      "72h_timeline": [
        {{"hours_from_now": 24, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 48, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 72, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}
      ],
      "projected_impact": {{
        "estimated_flood_area_km2": <float>,
        "estimated_affected_population": <int>,
        "infrastructure_risk": "<LOW|MODERATE|HIGH>",
        "evacuation_required": <bool>
      }},
      "final_risk_score_estimate": <float 0-100>
    }},
    "most_likely": {{
      "label": "Most Likely",
      "probability": <float 0.0-1.0>,
      "trigger_conditions": ["<specific meteorological/hydrological triggers>"],
      "72h_timeline": [
        {{"hours_from_now": 24, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 48, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 72, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}
      ],
      "projected_impact": {{
        "estimated_flood_area_km2": <float>,
        "estimated_affected_population": <int>,
        "infrastructure_risk": "<LOW|MODERATE|HIGH>",
        "evacuation_required": <bool>
      }},
      "final_risk_score_estimate": <float 0-100>
    }},
    "worst_case": {{
      "label": "Worst Case",
      "probability": <float 0.0-1.0>,
      "trigger_conditions": ["<specific meteorological/hydrological triggers>"],
      "72h_timeline": [
        {{"hours_from_now": 24, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 48, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}},
        {{"hours_from_now": 72, "description": "<what happens>", "river_level_change_m": <float>, "rainfall_expected_mm": <float>}}
      ],
      "projected_impact": {{
        "estimated_flood_area_km2": <float>,
        "estimated_affected_population": <int>,
        "infrastructure_risk": "<LOW|MODERATE|HIGH>",
        "evacuation_required": <bool>
      }},
      "final_risk_score_estimate": <float 0-100>
    }}
  }},
  "probability_validation_note": "<confirm probabilities sum to 1.0>",
  "dominant_uncertainty_factor": "<the single factor that most determines which scenario occurs>"
}}"""


async def run_scenario_generation(
    ai_provider: BaseAIProvider,
    risk_assessment: dict[str, Any],
    fact_sheet: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute CoT Step 3: Scenario Generation.

    Args:
        ai_provider: The active BaseAIProvider implementation.
        risk_assessment: Risk quantification output from Step 2.
        fact_sheet: Normalized fact sheet from Step 1.

    Returns:
        Validated scenario dict with three scenarios and timelines.

    Raises:
        ValueError: If JSON is invalid or probability constraint is violated.
    """
    district_context = {
        "name": fact_sheet.get("district_name"),
        "elevation_category": fact_sheet.get("topographical_risk_factors", {}).get("elevation_category"),
        "major_rivers": fact_sheet.get("geographic_context", {}).get("major_rivers", []),
        "historical_worst_event": fact_sheet.get("historical_flood_profile", {}).get("worst_event_severity"),
        "current_risk_category": risk_assessment.get("risk_category"),
        "composite_score": risk_assessment.get("composite_flood_risk_index"),
    }

    prompt = SCENARIO_TEMPLATE.format(
        district_name=fact_sheet.get("district_name", "Unknown"),
        risk_assessment=json.dumps(risk_assessment, indent=2),
        district_context=json.dumps(district_context, indent=2),
    )

    messages = [
        AIMessage(role="system", content=SYSTEM_PROMPT),
        AIMessage(role="user", content=prompt),
    ]

    response = await ai_provider.chat(
        messages=messages,
        temperature=0.15,  # Slightly higher for scenario diversity
        json_mode=True,
    )

    try:
        scenario_data = json.loads(response.content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Scenario generation returned invalid JSON: {exc}\n"
            f"Raw (first 500 chars): {response.content[:500]}"
        ) from exc

    # Validate probability constraint: must sum to ~1.0
    scenarios = scenario_data.get("scenarios", {})
    total_prob = sum(
        scenarios.get(s, {}).get("probability", 0.0)
        for s in ["best_case", "most_likely", "worst_case"]
    )

    if abs(total_prob - 1.0) > 0.05:
        # Normalize probabilities to sum to 1.0
        for scenario_key in ["best_case", "most_likely", "worst_case"]:
            if scenario_key in scenarios and total_prob > 0:
                scenarios[scenario_key]["probability"] = round(
                    scenarios[scenario_key]["probability"] / total_prob, 3
                )

    return scenario_data
