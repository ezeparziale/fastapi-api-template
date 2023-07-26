from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.user import UserOut


class PostBase(BaseModel):
    title: str = Field(title="Title of post", examples=["My post title"])
    content: str = Field(title="Content of post", examples=["My post content"])
    published: bool = Field(
        True,
        title="Published",
        description="Specifies whether the post has been published or not",
        examples=[True],
    )


class PostCreateIn(PostBase):
    pass


class PostUpdateIn(PostBase):
    pass


class PostUpdateOut(PostBase):
    model_config = ConfigDict(from_attributes=True)


class NewPostOut(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(title="ID of the post", examples=["1"])
    created_at: datetime = Field(
        title="Created at",
        description="The date and time that the post was created",
        examples=["2023-05-04T01:05:54.988Z"],
    )
    updated_at: datetime = Field(
        title="Updated at",
        description="The date and time that the post was updated",
        examples=["2023-05-04T01:05:54.988Z"],
    )
    owner_id: int = Field(title="ID of the owner", examples=["1"])
    owner: UserOut


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    Post: NewPostOut
    votes: int = Field(title="Count of votes", examples=["1"])
