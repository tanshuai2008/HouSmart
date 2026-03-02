from fastapi import APIRouter, HTTPException, Query, status

from app.services.road_map import import_road_network

router = APIRouter(prefix="/api", tags=["road-map"])


@router.get("/road-map", status_code=status.HTTP_200_OK)
def road_map(
    place: str = Query(..., min_length=1),
):
    result = import_road_network(place=place)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
