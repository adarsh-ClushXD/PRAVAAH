"""
Reports API routes.

Handles generation and download of disaster intelligence reports in
both JSON and PDF formats. PDF generation uses ReportLab.
"""
import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.models.database_models import FloodAnalysis

router = APIRouter()


@router.get("/reports/{analysis_id}/json")
async def download_json_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Download the complete analysis as a structured JSON report."""
    record = await _get_analysis_record(analysis_id, db)

    report_payload = {
        "report_metadata": {
            "analysis_id": analysis_id,
            "district_id": record.district_id,
            "district_name": record.district_name,
            "generated_at": record.created_at.isoformat(),
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "format": "JSON",
            "ai_provider": record.ai_provider,
            "model": record.model_name,
        },
        "risk_summary": {
            "composite_flood_risk_index": record.composite_flood_risk_index,
            "risk_category": record.risk_category,
            "alert_level": record.alert_level,
            "confidence_score": record.confidence_score,
            "deployment_priority_rank": record.deployment_priority_rank,
        },
        "fact_sheet": record.get_fact_sheet(),
        "risk_assessment": record.get_risk_assessment(),
        "scenarios": record.get_scenarios(),
        "xai_report": record.get_xai_report(),
    }

    return JSONResponse(
        content=report_payload,
        headers={
            "Content-Disposition": (
                f'attachment; filename="pravaah_report_{record.district_id}_'
                f'{analysis_id}.json"'
            )
        },
    )


@router.get("/reports/{analysis_id}/pdf")
async def download_pdf_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> StreamingResponse:
    """Generate and download a formatted PDF disaster intelligence report."""
    record = await _get_analysis_record(analysis_id, db)
    xai = record.get_xai_report()
    risk = record.get_risk_assessment()

    pdf_buffer = _generate_pdf(record, xai, risk)

    return StreamingResponse(
        io.BytesIO(pdf_buffer),
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                f'attachment; filename="pravaah_report_{record.district_id}_'
                f'{analysis_id}.pdf"'
            )
        },
    )


async def _get_analysis_record(
    analysis_id: str, db: AsyncSession
) -> FloodAnalysis:
    """Fetch analysis record by ID or raise 404."""
    result = await db.execute(
        select(FloodAnalysis).where(FloodAnalysis.analysis_id == analysis_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=404, detail=f"Analysis '{analysis_id}' not found."
        )
    return record


def _generate_pdf(
    record: FloodAnalysis,
    xai: dict,
    risk: dict,
) -> bytes:
    """
    Generate a professional PDF report using ReportLab.

    The report includes:
      - PRAVAAH letterhead
      - Risk summary section
      - AI reasoning chain
      - Recommendations table
      - Confidence assessment
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "PravaahTitle",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#0B1426"),
        spaceAfter=4,
    )
    heading_style = ParagraphStyle(
        "PravaahHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#00D4FF"),
        spaceAfter=6,
        spaceBefore=12,
    )
    body_style = ParagraphStyle(
        "PravaahBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=4,
    )
    alert_colors = {
        "GREEN": colors.HexColor("#00E676"),
        "YELLOW": colors.HexColor("#FFB800"),
        "ORANGE": colors.HexColor("#FF6B00"),
        "RED": colors.HexColor("#FF2D55"),
        "PURPLE": colors.HexColor("#9C27B0"),
    }

    alert_level = record.alert_level
    alert_color = alert_colors.get(alert_level, colors.gray)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("PRAVAAH", title_style))
    story.append(Paragraph(
        "Predictive River and Atmospheric Vulnerability Analysis for Adaptive Hazard Management",
        body_style,
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#00D4FF")))
    story.append(Spacer(1, 0.3 * cm))

    # ── Report Metadata ───────────────────────────────────────────────────────
    story.append(Paragraph(
        f"<b>District Intelligence Report: {record.district_name}</b>",
        heading_style,
    ))
    meta_data = [
        ["Analysis ID", record.analysis_id],
        ["Generated", record.created_at.strftime("%Y-%m-%d %H:%M UTC")],
        ["AI Provider", f"{record.ai_provider} / {record.model_name}"],
        ["Pipeline Duration", f"{record.pipeline_duration_seconds:.1f}s"],
    ]
    meta_table = Table(meta_data, colWidths=[4 * cm, 12 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.gray),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Risk Summary ──────────────────────────────────────────────────────────
    story.append(Paragraph("Risk Summary", heading_style))
    risk_data = [
        ["Composite Flood Risk Index", f"{record.composite_flood_risk_index:.1f} / 100"],
        ["Risk Category", record.risk_category],
        ["Alert Level", record.alert_level],
        ["Confidence Score", f"{record.confidence_score:.0%}"],
        ["Deployment Priority", f"Rank #{record.deployment_priority_rank or 'N/A'}"],
    ]
    risk_table = Table(risk_data, colWidths=[6 * cm, 10 * cm])
    risk_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8F4F8")),
        ("BACKGROUND", (1, 2), (1, 2), alert_color),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Executive Summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(xai.get("executive_summary", ""), body_style))

    # ── Reasoning Chain ───────────────────────────────────────────────────────
    story.append(Paragraph("AI Reasoning Chain (Explainability)", heading_style))
    for step in xai.get("reasoning_chain", []):
        story.append(Paragraph(
            f"<b>Step {step.get('step', '?')}: {step.get('title', '')}</b>",
            body_style,
        ))
        story.append(Paragraph(
            f"<i>Observation:</i> {step.get('observation', '')}",
            body_style,
        ))
        story.append(Paragraph(
            f"<i>Implication:</i> {step.get('implication', '')}",
            body_style,
        ))
        story.append(Spacer(1, 0.2 * cm))

    # ── Recommendations ───────────────────────────────────────────────────────
    story.append(Paragraph("Priority Recommendations", heading_style))
    rec_headers = [["Priority", "Category", "Action", "Timeframe", "Agency"]]
    rec_rows = [
        [
            f"#{r.get('priority', '?')}",
            r.get("category", ""),
            Paragraph(r.get("action", ""), body_style),
            r.get("timeframe", ""),
            r.get("responsible_agency", ""),
        ]
        for r in xai.get("recommendations", [])
    ]
    if rec_rows:
        rec_table = Table(
            rec_headers + rec_rows,
            colWidths=[1.5 * cm, 3 * cm, 7 * cm, 2.5 * cm, 3 * cm],
        )
        rec_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B1426")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(rec_table)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph(
        f"Generated by PRAVAAH AI Platform | Powered by Gemma 4 (31B) | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        ParagraphStyle("footer", parent=body_style, fontSize=8, textColor=colors.gray),
    ))

    doc.build(story)
    return buffer.getvalue()
