from datetime import UTC, datetime

import psutil
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.schemas import APIStatus

router = APIRouter()


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "API is healthy",
            "model": APIStatus,
        },
        503: {
            "description": "API is unhealthy or some services are down",
            "model": APIStatus,
        },
    },
)
def health_api(
    response: Response,
    db: Session = Depends(get_db),
) -> APIStatus:
    """
    ### Get api health
    """
    process = psutil.Process()
    start_time = process.create_time()

    timestamp = datetime.now(UTC).isoformat()
    uptime = str(datetime.now().timestamp() - start_time)

    api_status = "healthy"
    try:
        db.execute(text("SELECT 1")).scalars().first()
        db_status = "healthy"
    except SQLAlchemyError:
        db_status = "unhealthy"
        api_status = "unhealthy"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    resp = APIStatus(
        environment=settings.ENVIRONMENT,
        status=api_status,
        db_status=db_status,
        timestamp=timestamp,
        version=settings.VERSION,
        uptime=uptime,
    )

    return resp
