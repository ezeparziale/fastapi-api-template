from pydantic import BaseModel, Field


class APIStatus(BaseModel):
    status: str = Field(
        description="Represents the health status of the API", examples=["Healthy"]
    )
    db_status: str = Field(
        description="Represents the health status of the data base",
        examples=["Healthy", "Unhealthy"],
    )
    timestamp: str = Field(
        description="Represents the timestamp when the /health response was generated",
        examples=["2023-05-12T12:34:56.789Z"],
    )
    version: str = Field(
        description="Represents the version of the API", examples=["1.0.0"]
    )
    uptime: str = Field(
        description="Represents the API's uptime in seconds", examples=["1234.56789"]
    )
