from pydantic import BaseModel, Field
from pydantic.types import conint


class Vote(BaseModel):
    post_id: int = Field(title="ID of the post", example="1")
    dir: conint(le=1) = Field(
        title="Vote direction",
        description="Indicates the direction of the vote. 1 for an upvote, 0 for a downvote.",
        example=1,
    )
