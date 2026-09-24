from fastapi import APIRouter
from caraquista_api.schemas import HealthResponse

router = APIRouter(tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def get_health():
    """Chequeo de salud del servicio backend de República Caraquista."""
    return HealthResponse()
