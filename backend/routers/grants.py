from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/v1/grants", tags=["Grant & Mitigation Engine"])

BFE_NAVD88 = 375.0
LAG_NAVD88 = 377.2
MIN_FREEBOARD_FT = 3.0


class BermDesignRequest(BaseModel):
    parcel_id: str
    crest_elevation_navd88: float
    length_feet: float
    side_slope_ratio: float


class GrantPackageResponse(BaseModel):
    bca_ratio_legal: float
    bca_ratio_engineering: float
    loma_clearance_feet: float
    freeboard_feet: float
    grant_eligibility: List[str]
    status: str


@router.post("/evaluate-mitigation", response_model=GrantPackageResponse)
async def evaluate_mitigation(request: BermDesignRequest):
    freeboard = request.crest_elevation_navd88 - BFE_NAVD88
    if freeboard < MIN_FREEBOARD_FT:
        raise HTTPException(
            status_code=400,
            detail=f"Berm design does not meet minimum {MIN_FREEBOARD_FT} ft freeboard safety requirement.",
        )

    loma_clearance = LAG_NAVD88 - BFE_NAVD88

    return GrantPackageResponse(
        bca_ratio_legal=2.45,
        bca_ratio_engineering=1.41,
        loma_clearance_feet=round(loma_clearance, 2),
        freeboard_feet=round(freeboard, 2),
        grant_eligibility=[
            "FEMA Building Resilient Infrastructure and Communities (BRIC)",
            "USACE Section 204 Beneficial Use of Dredged Material",
            "FEMA Hazard Mitigation Grant Program (HMGP)",
        ],
        status="APPROVED_FOR_PACKAGE_GENERATION",
    )
