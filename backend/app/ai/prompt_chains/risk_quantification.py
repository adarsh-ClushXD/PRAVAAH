"""
CoT Step 2: Risk Quantification Prompt Chain.

Takes the normalized fact sheet from Step 1 and performs multi-dimensional
risk quantification. Gemma assigns scores across 5 risk dimensions and
computes a weighted composite flood risk index.

The 31B model's reasoning depth allows it to identify non-obvious risk
combinations (e.g., moderate rainfall + already-saturated soil + river at
warning level = high composite risk even if each factor alone is moderate).

Scoring dimensions:
  1. Atmospheric Risk (0-10): Rainfall intensity, humidity, storm probability
  2. River Overflow Risk (0-10): Current vs danger levels, trend, discharge
  3. Historical Vulnerability (0-10): Frequency, severity, recency weighting
  4. Topographical Risk (0-10): Elevation, proximity to rivers, drainage
  5. Saturation Risk (0-10): 30-day cumulative rainfall vs normal
"""
import json
from typing import Any

from app.ai.base_provider import AIMessage, BaseAIProvider


SYSTEM_PROMPT = """You are PRAVAAH's Risk Quantification Engine — a specialized hydrometeorological risk analyst for West Bengal flood assessment.

Your task is to ONLY quantify flood risk across defined dimensions using the provided fact sheet. Each score must be grounded in specific data from the fact sheet.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no prose, no code fences.
2. Every score must cite the specific data value that most influenced it.
3. Scores are 0.0–10.0 (float, one decimal place). 0=no risk, 10=maximum risk.
4. The composite_flood_risk_index is the authoritative risk score (0-100).
5. confidence_score (0.0–1.0) reflects data completeness and reliability.
6. Never assign a score above 8.0 unless multiple high-risk indicators converge.
7. All mathematical reasoning must be explicit in the rationale fields.
"""

RISK_QUANTIFICATION_TEMPLATE = """Quantify the flood risk for {district_name} district using the following normalized fact sheet.

=== FACT SHEET (Step 1 Output) ===
{fact_sheet}

=== SCORING METHODOLOGY ===

ATMOSPHERIC RISK (0-10):
  - 0-2: <50mm forecast 7-day total, no storm probability
  - 3-5: 50-150mm forecast, 30-60% storm probability  
  - 6-8: 150-300mm forecast, >60% storm probability
  - 9-10: >300mm forecast, active cyclone/depression influence

RIVER OVERFLOW RISK (0-10):
  - 0-3: All stations below warning level (ratio < 0.5)
  - 4-6: 1+ stations at warning, rising trend (ratio 0.5-0.85)
  - 7-8: 1+ stations at/near danger level (ratio 0.85-1.0)
  - 9-10: Station(s) above danger level (ratio > 1.0)

HISTORICAL VULNERABILITY (0-10):
  - Direct mapping: historical_risk_score from fact sheet × 1.0
  - Boost by 1.0 if any catastrophic event in last 5 years

TOPOGRAPHICAL RISK (0-10):
  - Based on base_flood_risk_multiplier: (multiplier - 1.0) × 10
  - Coastal/low-elevation districts get +1.5 bonus
  - High-elevation highland districts get -2.0 reduction

SATURATION RISK (0-10):
  - 30-day rainfall vs typical: <100mm=2, 100-200mm=4, 200-400mm=6, 400-600mm=8, >600mm=10
  - Add 1.0 if consecutive_high_rain_days ≥ 3
  - Add 1.5 if consecutive_high_rain_days ≥ 5

COMPOSITE INDEX FORMULA:
  composite = (
    atmospheric_risk × 0.25 +
    river_overflow_risk × 0.30 +
    historical_vulnerability × 0.15 +
    topographical_risk × 0.10 +
    saturation_risk × 0.20
  ) × 10

  Apply base_flood_risk_multiplier: composite × min(multiplier, 1.5)
  Final: clamp to 0–100, round to 1 decimal place.

=== REQUIRED OUTPUT SCHEMA ===
{{
  "district_id": "<string>",
  "risk_dimensions": {{
    "atmospheric_risk": {{
      "score": <float 0-10>,
      "rationale": "<1-2 sentences citing specific data values>",
      "key_driver": "<the single most important contributing factor>"
    }},
    "river_overflow_risk": {{
      "score": <float 0-10>,
      "rationale": "<1-2 sentences citing specific data values>",
      "key_driver": "<the single most important contributing factor>"
    }},
    "historical_vulnerability": {{
      "score": <float 0-10>,
      "rationale": "<1-2 sentences citing specific data values>",
      "key_driver": "<the single most important contributing factor>"
    }},
    "topographical_risk": {{
      "score": <float 0-10>,
      "rationale": "<1-2 sentences citing specific data values>",
      "key_driver": "<the single most important contributing factor>"
    }},
    "saturation_risk": {{
      "score": <float 0-10>,
      "rationale": "<1-2 sentences citing specific data values>",
      "key_driver": "<the single most important contributing factor>"
    }}
  }},
  "composite_calculation": {{
    "weighted_atmospheric": <float>,
    "weighted_river": <float>,
    "weighted_historical": <float>,
    "weighted_topographical": <float>,
    "weighted_saturation": <float>,
    "pre_multiplier_score": <float>,
    "base_risk_multiplier_applied": <float>,
    "final_composite_index": <float 0-100>
  }},
  "composite_flood_risk_index": <float 0-100>,
  "risk_category": "<LOW|MODERATE|HIGH|VERY HIGH|CRITICAL>",
  "confidence_score": <float 0.0-1.0>,
  "confidence_rationale": "<explain what reduces confidence, if anything>",
  "converging_risk_factors": ["<list of 2-4 most dangerous combined factors>"],
  "primary_risk_driver": "<the single most critical risk factor for this district>"
}}"""


RISK_CATEGORIES = [
    (0, 20, "LOW"),
    (20, 40, "MODERATE"),
    (40, 60, "HIGH"),
    (60, 80, "VERY HIGH"),
    (80, 100, "CRITICAL"),
]


def classify_risk_category(composite_score: float) -> str:
    """Map a composite score (0-100) to a risk category label."""
    for low, high, label in RISK_CATEGORIES:
        if low <= composite_score < high:
            return label
    return "CRITICAL"


async def run_risk_quantification(
    ai_provider: BaseAIProvider,
    fact_sheet: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute CoT Step 2: Risk Quantification.

    Args:
        ai_provider: The active BaseAIProvider implementation.
        fact_sheet: The normalized fact sheet from Step 1.

    Returns:
        Validated risk quantification dict with composite score.

    Raises:
        ValueError: If Gemma returns invalid JSON or missing required fields.
    """
    prompt = RISK_QUANTIFICATION_TEMPLATE.format(
        district_name=fact_sheet.get("district_name", "Unknown"),
        fact_sheet=json.dumps(fact_sheet, indent=2),
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
        risk_data = json.loads(response.content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Risk quantification returned invalid JSON: {exc}\n"
            f"Raw (first 500 chars): {response.content[:500]}"
        ) from exc

    # Validate and enforce required fields
    required_fields = [
        "district_id", "risk_dimensions", "composite_flood_risk_index",
        "risk_category", "confidence_score",
    ]
    missing = [f for f in required_fields if f not in risk_data]
    if missing:
        raise ValueError(f"Risk quantification missing required fields: {missing}")

    # Normalize composite score bounds
    risk_data["composite_flood_risk_index"] = round(
        max(0.0, min(float(risk_data["composite_flood_risk_index"]), 100.0)), 1
    )

    # Validate risk category against computed score
    expected_category = classify_risk_category(risk_data["composite_flood_risk_index"])
    if risk_data.get("risk_category") != expected_category:
        risk_data["risk_category"] = expected_category

    return risk_data
