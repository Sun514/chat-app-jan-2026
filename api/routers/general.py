"""General endpoints: health, version, etc."""

from fastapi import APIRouter

from api.config import settings
from api.core.database import get_pool

router = APIRouter(tags=["general"])


@router.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
    }


@router.get("/version")
async def version():
    """Version information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
    }
