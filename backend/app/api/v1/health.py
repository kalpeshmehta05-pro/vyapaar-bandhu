"""
VyapaarBandhu -- Health Check Endpoints
Liveness, readiness, and detailed health checks for production monitoring.
"""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter

from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


async def _check_database() -> str:
    """Check database connectivity with SELECT 1."""
    try:
        from app.db.session import get_async_session

        async for db in get_async_session():
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
            return "healthy"
    except Exception as e:
        logger.warning("health.db_check_failed", error=str(e))
        return "unhealthy"


async def _check_redis() -> str:
    """Check Redis connectivity with PING."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        await r.aclose()
        return "healthy"
    except Exception as e:
        logger.warning("health.redis_check_failed", error=str(e))
        return "unhealthy"


async def _check_celery() -> str:
    """Check if Celery workers are active (2s timeout)."""
    try:
        from app.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2)
        active = inspect.active()
        if active:
            return "healthy"
        return "unhealthy"
    except Exception as e:
        logger.warning("health.celery_check_failed", error=str(e))
        return "unhealthy"


@router.get("/health")
async def health_check():
    """
    Detailed health check. Returns 503 if any critical service is down.
    """
    db_status = await _check_database()
    redis_status = await _check_redis()
    celery_status = await _check_celery()

    checks = {
        "database": db_status,
        "redis": redis_status,
        "celery": celery_status,
    }

    all_healthy = all(v == "healthy" for v in [db_status, redis_status])
    status_code = 200 if all_healthy else 503

    from starlette.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if all_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": settings.APP_VERSION,
            "checks": checks,
        },
    )


@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe. 200 if DB + Redis connected."""
    db_status = await _check_database()
    redis_status = await _check_redis()

    if db_status == "healthy" and redis_status == "healthy":
        return {"status": "ready"}

    from starlette.responses import JSONResponse

    return JSONResponse(status_code=503, content={"status": "not ready"})


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe. Always 200 if process is running."""
    return {"status": "alive"}
