from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.db.session import check_database_connection
from app.schemas.health import HealthResponse

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health_check(response: Response) -> HealthResponse:
    settings = get_settings()
    database_ok = check_database_connection()

    if not database_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if database_ok else "degraded",
        service="ecommerce-mvp-api",
        version=settings.app_version,
        database="ok" if database_ok else "unavailable",
        mock_mode=settings.mock_mode,
    )
