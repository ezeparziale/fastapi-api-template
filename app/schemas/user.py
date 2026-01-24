from datetime import date, datetime
from typing import Any

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


class UserCreditCardIn(BaseModel):
    card_number: str = Field(
        title="Credit card number",
        description="The credit card number of the user",
        examples=["1234 5678 9012 3456"],
    )
    expiration_date: date = Field(
        title="Expiration date",
        description="The expiration date of the credit card",
        examples=["2023-05-04"],
    )
    cvv: str = Field(
        title="CVV",
        description="The CVV of the credit card",
        examples=["123"],
    )


class UserCreditCardOut(BaseModel):
    card_number: str = Field(
        title="Credit card number",
        description=(
            "The credit card number of the user, only showing the last four digits"
        ),
        examples=["**** **** **** 3456"],
    )
    expiration_date: date = Field(
        title="Expiration date",
        description="The expiration date of the credit card",
        examples=["2023-05-04"],
    )

    @staticmethod
    def mask_card_number(card_number: str) -> str:
        return "**** **** **** " + card_number[-4:]

    def __init__(self, **data: Any):
        super().__init__(**data)
        self.card_number = self.mask_card_number(self.card_number)
