from fastapi import APIRouter, HTTPException, Query, status

from app.services.noise_estimator import estimate_noise, estimate_noise_from_address

router = APIRouter(prefix="/api", tags=["noise-estimator"])


@router.get("/noise-estimate/address", status_code=status.HTTP_200_OK)
def noise_estimate_by_address(
    address: str = Query(..., min_length=1),
):
    result = estimate_noise_from_address(address=address)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result


@router.get("/noise-estimate/coordinates", status_code=status.HTTP_200_OK)
def noise_estimate_by_coordinates(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    result = estimate_noise(lat=lat, lon=lon)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
