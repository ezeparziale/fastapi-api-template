from pydantic import BaseModel


class Message(BaseModel):
    message: str


class MessageDetail(BaseModel):
    detail: str
