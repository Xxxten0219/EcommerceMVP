from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import create_all_tables
from app.db.session import SessionLocal
from app.services.seed import seed_demo_organization
from app.services.simulation import seed_demo_analytics

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.ensure_runtime_directories()
    create_all_tables()
    with SessionLocal() as session:
        seed_demo_organization(session)
        seed_demo_analytics(session)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "service": "ecommerce-mvp-api",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
