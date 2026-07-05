"""
CoT Step 4: XAI Report Generation Prompt Chain.

The final reasoning step. Gemma synthesizes all prior outputs into the
Explainable AI (XAI) report — a human-readable, structured intelligence
brief designed for district disaster management officials.

The XAI report MUST:
  1. Explain WHY the district has this risk level (not just that it does)
  2. Present step-by-step reasoning in plain language
  3. Provide prioritized, actionable recommendations
  4. Assign a final confidence score with a honest uncertainty disclosure
  5. Generate a natural language summary suitable for press release / SMS alert

Design principle: Every claim must trace back to specific data in the fact sheet.
This is the Explainability component — the antithesis of black-box AI.
"""
import json
from datetime import datetime, timezone
from typing import Any

from app.ai.base_provider import AIMessage, BaseAIProvider


SYSTEM_PROMPT = """You are PRAVAAH's Explainability Engine — a senior disaster intelligence analyst who writes decision-support reports for West Bengal district administrators and emergency responders.

Your task is to synthesize all prior analysis into a clear, actionable, and transparent intelligence report. This report will be read by government officials making decisions about evacuation orders and resource deployment.

CRITICAL RULES:
1. Output ONLY valid JSON — no markdown, no prose, no code fences.
2. Every reasoning step must cite SPECIFIC data values (never vague statements like "high rainfall").
3. Recommendations must be SPECIFIC and ACTIONABLE (not "prepare for flooding" but "pre-position 200 rescue boats at Murshidabad Ghat within 6 hours").
4. The confidence score must reflect genuine uncertainty — never inflate confidence.
5. The executive_summary must be written for a non-technical audience — clear, direct, no jargon.
6. This system is used for life-safety decisions. Accuracy and honesty outweigh optimism.
"""

XAI_REPORT_TEMPLATE = """Generate the final Explainable AI intelligence report for {district_name} district.

=== ANALYSIS PIPELINE OUTPUTS ===

--- FACT SHEET (Step 1) ---
{fact_sheet}

--- RISK QUANTIFICATION (Step 2) ---
{risk_assessment}

--- SCENARIO PROJECTIONS (Step 3) ---
{scenarios}

=== REPORT REQUIREMENTS ===

The report must include:
1. Executive Summary (2-3 sentences, plain language, for public/official communication)
2. Step-by-step reasoning chain (4-6 numbered steps explaining the risk derivation)  
3. Three prioritized, specific, actionable recommendations
4. Alert level and deployment priority
5. Final confidence score with honest uncertainty disclosure

=== REQUIRED OUTPUT SCHEMA ===
{{
  "district_id": "<string>",
  "district_name": "<string>",
  "report_generated_at": "<ISO datetime>",
  "alert_level": "<GREEN|YELLOW|ORANGE|RED|PURPLE>",
  "composite_flood_risk_index": <float 0-100>,
  "risk_category": "<LOW|MODERATE|HIGH|VERY HIGH|CRITICAL>",
  "confidence_score": <float 0.0-1.0>,
  "deployment_priority_rank": <int 1-10, where 1 = most urgent>,
  "executive_summary": "<2-3 sentence plain-language summary for officials/public>",
  "reasoning_chain": [
    {{
      "step": 1,
      "title": "<step title>",
      "observation": "<what the data shows (cite specific values)>",
      "implication": "<what this means for flood risk>"
    }},
    {{
      "step": 2,
      "title": "<step title>",
      "observation": "<what the data shows>",
      "implication": "<what this means>"
    }},
    {{
      "step": 3,
      "title": "<step title>",
      "observation": "<what the data shows>",
      "implication": "<what this means>"
    }},
    {{
      "step": 4,
      "title": "<step title>",
      "observation": "<what the data shows>",
      "implication": "<what this means>"
    }}
  ],
  "recommendations": [
    {{
      "priority": 1,
      "category": "<EVACUATION|INFRASTRUCTURE|MONITORING|COMMUNICATION|RESOURCE_DEPLOYMENT>",
      "action": "<specific, actionable instruction with numbers/locations/timeframes>",
      "responsible_agency": "<agency/department>",
      "timeframe": "<within X hours/days>",
      "rationale": "<why this action is needed now>"
    }},
    {{
      "priority": 2,
      "category": "<category>",
      "action": "<specific action>",
      "responsible_agency": "<agency>",
      "timeframe": "<timeframe>",
      "rationale": "<rationale>"
    }},
    {{
      "priority": 3,
      "category": "<category>",
      "action": "<specific action>",
      "responsible_agency": "<agency>",
      "timeframe": "<timeframe>",
      "rationale": "<rationale>"
    }}
  ],
  "key_risk_indicators": {{
    "primary_threat": "<the most critical current threat>",
    "secondary_threat": "<the second most critical threat>",
    "converging_factors": ["<list of compounding risk factors>"],
    "most_likely_impact_zone": "<specific area within district most at risk>"
  }},
  "confidence_assessment": {{
    "overall_confidence": <float 0.0-1.0>,
    "data_completeness": "<FULL|PARTIAL|SPARSE>",
    "uncertainty_sources": ["<what data gaps reduce confidence>"],
    "reliability_note": "<honest statement about what we know and don't know>"
  }},
  "sms_alert_text": "<under 160 characters: district, risk level, and 1 key action>"
}}"""


ALERT_LEVELS = {
    "LOW": "GREEN",
    "MODERATE": "YELLOW",
    "HIGH": "ORANGE",
    "VERY HIGH": "RED",
    "CRITICAL": "PURPLE",
}


async def run_xai_report(
    ai_provider: BaseAIProvider,
    fact_sheet: dict[str, Any],
    risk_assessment: dict[str, Any],
    scenarios: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute CoT Step 4: XAI Report Generation.

    The final step of the PRAVAAH AI pipeline. Produces the complete
    intelligence report that drives the dashboard display and PDF export.

    Args:
        ai_provider: The active BaseAIProvider implementation.
        fact_sheet: Normalized fact sheet from Step 1.
        risk_assessment: Risk quantification from Step 2.
        scenarios: Scenario projections from Step 3.

    Returns:
        Complete XAI intelligence report dict.

    Raises:
        ValueError: If the response JSON is invalid or required fields missing.
    """
    prompt = XAI_REPORT_TEMPLATE.format(
        district_name=fact_sheet.get("district_name", "Unknown"),
        fact_sheet=json.dumps(fact_sheet, indent=2),
        risk_assessment=json.dumps(risk_assessment, indent=2),
        scenarios=json.dumps(scenarios, indent=2),
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
        report = json.loads(response.content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"XAI report returned invalid JSON: {exc}\n"
            f"Raw (first 500 chars): {response.content[:500]}"
        ) from exc

    # Validate required fields
    required = [
        "district_id", "alert_level", "composite_flood_risk_index",
        "confidence_score", "executive_summary", "reasoning_chain",
        "recommendations",
    ]
    missing = [f for f in required if f not in report]
    if missing:
        raise ValueError(f"XAI report missing required fields: {missing}")

    # Enforce alert level consistency
    risk_category = risk_assessment.get("risk_category", "MODERATE")
    expected_alert = ALERT_LEVELS.get(risk_category, "YELLOW")
    report["alert_level"] = expected_alert

    # Inject report timestamp if missing
    if not report.get("report_generated_at"):
        report["report_generated_at"] = datetime.now(timezone.utc).isoformat()

    # Clamp confidence score
    report["confidence_score"] = round(
        max(0.0, min(float(report.get("confidence_score", 0.7)), 1.0)), 3
    )

    return report
