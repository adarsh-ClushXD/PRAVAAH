"""Analysis API routes — triggers AI pipeline and returns results."""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db_session
from app.geospatial.district_registry import DistrictRegistry
from app.models.pydantic_schemas import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisTriggerResponse,
)
from app.services.flood_analysis_service import FloodAnalysisService

router = APIRouter()


@router.post("/analysis/run", response_model=AnalysisResponse)
async def run_flood_analysis(
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisResponse:
    """
    Trigger a full AI analysis pipeline for a district.

    This is a synchronous endpoint — it runs the complete 4-step
    Gemma pipeline and returns the result. Expect 60-180 seconds
    for a 31B model running locally on Ollama.

    Set force_refresh=True to bypass the analysis cache.
    """
    # Validate district exists
    try:
        DistrictRegistry.get_district(request.district_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"District '{request.district_id}' not found in registry.",
        )

    service = FloodAnalysisService()

    try:
        result = await service.run_analysis(
            district_id=request.district_id,
            db=db,
            force_refresh=request.force_refresh,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"AI pipeline validation error: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis pipeline failed: {str(exc)}",
        )


@router.get(
    "/analysis/{district_id}/latest",
    response_model=AnalysisResponse | None,
)
async def get_latest_analysis(
    district_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisResponse | None:
    """
    Retrieve the most recent completed analysis for a district.

    Returns null (HTTP 200 with null body) if no analysis exists yet.
    Use POST /analysis/run to trigger a fresh analysis.
    """
    try:
        DistrictRegistry.get_district(district_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"District '{district_id}' not found.",
        )

    service = FloodAnalysisService()
    return await service.get_latest_analysis(district_id, db)
