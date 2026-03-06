# HouSmart/backend/app/api/routes/health.py
from fastapi import APIRouter

router = APIRouter(prefix="/api")

@router.get("/health", summary="Service health check")
def health_check():
    """
    Health probe endpoint that confirms the API process is up and able to serve requests.

    Input:
    - No request body or query parameters.

    Output:
    - JSON with service heartbeat metadata:
      - status: fixed value "ok"
      - service: service identifier string

    How it is calculated:
    - Returns a static in-memory response; no database or external API calls.

    What can be extracted:
    - Basic liveness signal for load balancers, uptime checks, and deployment smoke tests.
    """
    return {
        "status": "ok",
        "service": "HouSmart Backend"
    }
