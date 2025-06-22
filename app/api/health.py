from datetime import UTC, datetime

import psutil
from fastapi import APIRouter, Depends, status
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
            "description": "Api status",
            "model": APIStatus,
        },
    },
)
def health_api(db: Session = Depends(get_db)) -> APIStatus:
    """
    ### Get api health
    """
    process = psutil.Process()
    start_time = process.create_time()

    timestamp = datetime.now(UTC).isoformat()
    uptime = str(datetime.now().timestamp() - start_time)

    try:
        db.execute(text("SELECT 1")).scalars().first()
        db_status = "Healthy"
    except SQLAlchemyError:
        db_status = "Unhealthy"

    resp = APIStatus(
        environment=settings.ENVIRONMENT,
        status="Healthy",
        db_status=db_status,
        timestamp=timestamp,
        version=settings.VERSION,
        uptime=uptime,
    )

    return resp
