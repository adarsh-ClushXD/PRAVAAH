"""Rivers API routes."""
from fastapi import APIRouter, HTTPException

from app.data_ingestion.river_gauge_fetcher import RiverGaugeFetcher, DataFetchError
from app.models.pydantic_schemas import DistrictRiverSummary, RiverStationResponse

router = APIRouter()


@router.get("/rivers", response_model=list[RiverStationResponse])
async def list_all_river_stations() -> list[RiverStationResponse]:
    """Return all river gauge stations with current readings and risk ratios."""
    fetcher = RiverGaugeFetcher()
    try:
        stations = await fetcher.fetch()
        return [RiverStationResponse(**s) for s in stations]
    except DataFetchError as exc:
        raise HTTPException(status_code=503, detail=f"River data unavailable: {exc.message}")


@router.get("/rivers/district/{district_id}", response_model=DistrictRiverSummary)
async def get_district_river_summary(district_id: str) -> DistrictRiverSummary:
    """Return all river stations for a district with overflow risk summary."""
    fetcher = RiverGaugeFetcher()
    try:
        risk_summary = await fetcher.fetch_all_with_risk()
        district_data = risk_summary.get(district_id)

        if not district_data:
            return DistrictRiverSummary(
                district_id=district_id,
                max_overflow_risk=0.0,
                critical_stations=0,
                warning_stations=0,
                stations=[],
            )

        return DistrictRiverSummary(
            district_id=district_id,
            max_overflow_risk=district_data["max_overflow_risk"],
            critical_stations=district_data["critical_stations"],
            warning_stations=district_data["warning_stations"],
            stations=[RiverStationResponse(**s) for s in district_data["stations"]],
        )
    except DataFetchError as exc:
        raise HTTPException(status_code=503, detail=f"River data unavailable: {exc.message}")


@router.get("/rivers/station/{station_id}", response_model=RiverStationResponse)
async def get_station_detail(station_id: str) -> RiverStationResponse:
    """Return details for a single river gauge station."""
    fetcher = RiverGaugeFetcher()
    try:
        all_stations = await fetcher.fetch()
        station = next((s for s in all_stations if s["station_id"] == station_id), None)
        if not station:
            raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found.")
        return RiverStationResponse(**station)
    except DataFetchError as exc:
        raise HTTPException(status_code=503, detail=f"River data unavailable: {exc.message}")
