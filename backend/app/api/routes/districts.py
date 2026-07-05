"""Districts API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.geospatial.district_registry import DistrictRegistry
from app.models.database_models import FloodAnalysis
from app.models.pydantic_schemas import DistrictDetail, DistrictSummary

router = APIRouter()


@router.get("/districts", response_model=list[DistrictSummary])
async def list_all_districts(
    db: AsyncSession = Depends(get_db_session),
) -> list[DistrictSummary]:
    """
    Return all 23 West Bengal districts with their latest risk scores.

    Districts without an analysis return base metadata only.
    Used to populate the Leaflet map and risk matrix table.
    """
    all_districts = DistrictRegistry.get_all_districts()

    # Fetch latest analysis for each district in a single query
    result = await db.execute(
        select(FloodAnalysis)
        .where(FloodAnalysis.is_latest == True)  # noqa: E712
        .order_by(FloodAnalysis.composite_flood_risk_index.desc())
    )
    latest_analyses = {r.district_id: r for r in result.scalars().all()}

    summaries = []
    for district in all_districts:
        analysis = latest_analyses.get(district.id)
        xai = analysis.get_xai_report() if analysis else {}

        summaries.append(
            DistrictSummary(
                district_id=district.id,
                district_name=district.name,
                lat=district.lat,
                lon=district.lon,
                composite_flood_risk_index=(
                    analysis.composite_flood_risk_index if analysis else None
                ),
                risk_category=analysis.risk_category if analysis else None,
                alert_level=analysis.alert_level if analysis else None,
                confidence_score=analysis.confidence_score if analysis else None,
                primary_threat=xai.get("key_risk_indicators", {}).get("primary_threat"),
                last_analyzed_at=analysis.created_at if analysis else None,
                major_rivers=district.major_rivers,
                base_flood_risk=district.base_flood_risk,
            )
        )

    # Sort by risk (analyzed districts first, then by score desc)
    summaries.sort(
        key=lambda d: (d.composite_flood_risk_index is None, -(d.composite_flood_risk_index or 0))
    )
    return summaries


@router.get("/districts/{district_id}", response_model=DistrictDetail)
async def get_district_detail(
    district_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> DistrictDetail:
    """Return full district metadata and latest analysis."""
    try:
        district = DistrictRegistry.get_district(district_id)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"District '{district_id}' not found."
        )

    result = await db.execute(
        select(FloodAnalysis)
        .where(
            FloodAnalysis.district_id == district_id,
            FloodAnalysis.is_latest == True,  # noqa: E712
        )
        .limit(1)
    )
    analysis_record = result.scalar_one_or_none()

    latest_analysis = None
    if analysis_record:
        from app.services.flood_analysis_service import FloodAnalysisService
        service = FloodAnalysisService()
        latest_analysis = service._build_response(
            analysis_id=analysis_record.analysis_id,
            district_id=analysis_record.district_id,
            district_name=analysis_record.district_name,
            xai_report=analysis_record.get_xai_report(),
            risk_assessment=analysis_record.get_risk_assessment(),
            scenarios=analysis_record.get_scenarios(),
            pipeline_duration=analysis_record.pipeline_duration_seconds,
            created_at=analysis_record.created_at,
        )

    return DistrictDetail(
        district_id=district.id,
        district_name=district.name,
        lat=district.lat,
        lon=district.lon,
        elevation_m=district.elevation_m,
        area_km2=district.area_km2,
        population_density=district.population_density,
        division=district.division,
        major_rivers=district.major_rivers,
        base_flood_risk=district.base_flood_risk,
        latest_analysis=latest_analysis,
    )
