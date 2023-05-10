from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.user import UserOut


class PostBase(BaseModel):
    title: str = Field(title="Title of post", example="My post title")
    content: str = Field(title="Content of post", example="My post content")
    published: bool = Field(
        True,
        title="Published",
        description="Specifies whether the post has been published or not",
        example=True,
    )


class PostCreateIn(PostBase):
    pass

class PostUpdateIn(PostBase):
    pass

class PostUpdateOut(PostBase):
    class Config:
        orm_mode = True


class NewPostOut(PostBase):
    id: int = Field(title="ID of the post", example="1")
    created_at: datetime = Field(
        title="Created at",
        description="The date and time that the post was created",
        example="2023-05-04T01:05:54.988Z",
    )
    owner_id: int = Field(title="ID of the owner", example="1")
    owner: UserOut

    class Config:
        orm_mode = True


class PostOut(BaseModel):
    Post: NewPostOut
    votes: int = Field(title="Count of votes", example="1")

    class Config:
        orm_mode = True
