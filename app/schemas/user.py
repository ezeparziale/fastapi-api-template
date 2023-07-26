from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="ID of the user", examples=["1"])
    email: EmailStr = Field(title="Email of the user", examples=["user@example.com"])
    created_at: datetime = Field(
        title="Created at",
        description="The date and time that the user was created",
        examples=["2023-05-04T01:05:54.988Z"],
    )
    updated_at: datetime = Field(
        title="Updated at",
        description="The date and time that the user was updated",
        examples=["2023-05-04T01:05:54.988Z"],
    )


class UserCreate(BaseModel):
    email: EmailStr = Field(title="Email of the user", examples=["user@example.com"])
    password: str = Field(title="Pasword of the user", examples=["secret_password"])
