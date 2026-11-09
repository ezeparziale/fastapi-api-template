from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class APIStatusOut(BaseModel):
    """Response model for the legacy `/health` endpoint.

    Kept for backward compatibility with the Docker healthcheck and existing
    clients. It reports the database status only; prefer `LivenessOut` or
    `ReadinessOut` for new integrations.
    """

    environment: str = Field(
        description="Represents the environment in which the API is running",
        examples=["local", "staging", "production"],
    )
    status: Literal["healthy", "unhealthy"] = Field(
        description="Represents the health status of the API",
        examples=["healthy", "unhealthy"],
    )
    db_status: Literal["healthy", "unhealthy"] = Field(
        description="Represents the health status of the data base",
        examples=["healthy", "unhealthy"],
    )
    timestamp: datetime = Field(
        description="Represents the timestamp when the /health response was generated",
        examples=["2023-05-12T12:34:56.789Z"],
    )
    version: str = Field(
        description="Represents the version of the API", examples=["1.0.0"]
    )
    uptime: str = Field(
        description="Represents the API's uptime in seconds", examples=["1234.56789"]
    )


class LivenessOut(BaseModel):
    """Response model for the `/health/live` liveness probe.

    Liveness only confirms that the process is running. It never checks the
    database or the cache, so a dependency outage cannot cause the orchestrator
    to restart the container.
    """

    status: Literal["alive"] = Field(
        description="Indicates that the process is alive",
        examples=["alive"],
    )
    version: str = Field(
        description="Represents the version of the API", examples=["1.0.0"]
    )
    timestamp: datetime = Field(
        description="Timestamp when the /health/live response was generated",
        examples=["2023-05-12T12:34:56.789Z"],
    )


class ReadinessOut(BaseModel):
    """Response model for the `/health/ready` readiness probe.

    Readiness reports whether the API can receive traffic. The database is a
    required dependency, while the cache is optional: a Redis outage is shown in
    `redis_status` but does not make the API unready.
    """

    environment: str = Field(
        description="Represents the environment in which the API is running",
        examples=["local", "staging", "production"],
    )
    status: Literal["healthy", "unhealthy"] = Field(
        description="Indicates whether the API is ready to receive traffic",
        examples=["healthy", "unhealthy"],
    )
    db_status: Literal["healthy", "unhealthy"] = Field(
        description="Represents the health status of the database",
        examples=["healthy", "unhealthy"],
    )
    redis_status: Literal["healthy", "unhealthy", "disabled"] = Field(
        description=(
            "Represents the health status of Redis. It is `disabled` when "
            "caching is turned off."
        ),
        examples=["healthy", "unhealthy", "disabled"],
    )
    timestamp: datetime = Field(
        description="Timestamp when the /health/ready response was generated",
        examples=["2023-05-12T12:34:56.789Z"],
    )
    version: str = Field(
        description="Represents the version of the API", examples=["1.0.0"]
    )
    uptime: str = Field(
        description="Represents the API's uptime in seconds", examples=["1234.56789"]
    )
