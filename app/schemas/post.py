from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserOut


class PostBase(BaseModel):
    title: str
    content: str
    published: bool = True


class PostCreate(PostBase):
    pass


class Post(PostBase):
    id: int
    created_at: datetime
    owner_id: int
    owner: UserOut

    class Config:
        orm_mode = True


class PostOUT(BaseModel):
    Post: Post
    votes: int

    class Config:
        orm_mode = True
