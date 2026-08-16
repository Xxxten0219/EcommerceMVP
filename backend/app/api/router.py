from fastapi import APIRouter

from app.api.v1.communication import router as communication_router
from app.api.v1.health import router as health_router
from app.api.v1.imports import router as imports_router
from app.api.v1.organization import router as organization_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(organization_router)
api_router.include_router(communication_router)
api_router.include_router(imports_router)
