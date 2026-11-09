from datetime import UTC, datetime
from typing import Literal

import psutil
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api.deps import CacheDep
from app.core.config import settings
from app.db.database import get_db
from app.schemas import APIStatusOut, LivenessOut, ReadinessOut

router = APIRouter()


def _uptime() -> str:
    """Return the current process uptime, in seconds, as a string."""
    return str(datetime.now().timestamp() - psutil.Process().create_time())


def _db_is_healthy(db: Session) -> bool:
    """Check the database connection with a lightweight query.

    Args:
        db: A SQLAlchemy session bound to the application database.

    Returns:
        bool: `True` when `SELECT 1` succeeds, `False` on any SQLAlchemy error.
    """
    try:
        db.execute(text("SELECT 1")).scalars().first()
    except SQLAlchemyError:
        return False
    return True


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_model=APIStatusOut,
    summary="Legacy health check",
    responses={
        200: {
            "description": "API is healthy",
            "model": APIStatusOut,
        },
        503: {
            "description": "API is unhealthy or some services are down",
            "model": APIStatusOut,
        },
    },
)
def health_api(
    response: Response,
    db: Session = Depends(get_db),
) -> APIStatusOut:
    """
    Checks the database connection and returns `503` when it is unreachable.

    Kept for backward compatibility. Prefer `/health/live` for liveness checks
    and `/health/ready` for readiness checks.
    """
    db_healthy = _db_is_healthy(db)
    api_status: Literal["healthy", "unhealthy"] = (
        "healthy" if db_healthy else "unhealthy"
    )

    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return APIStatusOut(
        environment=settings.ENVIRONMENT,
        status=api_status,
        db_status="healthy" if db_healthy else "unhealthy",
        timestamp=datetime.now(UTC),
        version=settings.VERSION,
        uptime=_uptime(),
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    response_model=LivenessOut,
    summary="Liveness probe",
    responses={
        200: {
            "description": "API process is alive",
            "model": LivenessOut,
        },
    },
)
async def health_live() -> LivenessOut:
    """
    Confirms that the API process is running.

    It does not depend on the database or the cache, so an outage in those
    services does not mark the process as unhealthy. Returns `200` with
    `status: "alive"` while the process is up.
    """
    return LivenessOut(
        status="alive",
        version=settings.VERSION,
        timestamp=datetime.now(UTC),
    )


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    response_model=ReadinessOut,
    summary="Readiness probe",
    responses={
        200: {
            "description": "API is ready to receive traffic",
            "model": ReadinessOut,
        },
        503: {
            "description": "API is not ready: the database is unavailable",
            "model": ReadinessOut,
        },
    },
)
async def health_ready(
    response: Response,
    cache: CacheDep,
    db: Session = Depends(get_db),
) -> ReadinessOut:
    """
    Reports whether the API is ready to receive traffic.

    - The **database** is required: if it is unreachable the response is `503`
      and `db_status` is `unhealthy`.
    - The **cache** is optional: a Redis outage is reported in `redis_status`
      but does not make the API unready. When caching is disabled,
      `redis_status` is `disabled`.

    Returns `200` when ready and `503` when the database is unavailable.
    """
    db_healthy = await run_in_threadpool(_db_is_healthy, db)

    redis_status: Literal["healthy", "unhealthy", "disabled"]
    if settings.CACHE_ENABLED:
        redis_healthy = await cache.health_check()
        redis_status = "healthy" if redis_healthy else "unhealthy"
    else:
        redis_status = "disabled"

    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessOut(
        environment=settings.ENVIRONMENT,
        status="healthy" if db_healthy else "unhealthy",
        db_status="healthy" if db_healthy else "unhealthy",
        redis_status=redis_status,
        timestamp=datetime.now(UTC),
        version=settings.VERSION,
        uptime=_uptime(),
    )
