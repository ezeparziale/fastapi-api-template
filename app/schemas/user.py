from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int = Field(title="ID of the user", example="1")
    email: EmailStr = Field(title="Email of the user", example="user@example.com")
    created_at: datetime = Field(
        title="Created at",
        description="The date and time that the user was created",
        example="2023-05-04T01:05:54.988Z",
    )
    updated_at: datetime = Field(
        title="Updated at",
        description="The date and time that the user was updated",
        example="2023-05-04T01:05:54.988Z",
    )

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr = Field(title="Email of the user", example="user@example.com")
    password: str = Field(title="Pasword of the user", example="secret_password")
