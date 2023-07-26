from pydantic import BaseModel, Field


class Message(BaseModel):
    message: str = Field(title="Message information")


class MessageDetail(BaseModel):
    detail: str = Field(title="Message detail")
