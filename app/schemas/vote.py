from typing import Annotated

from pydantic import BaseModel, Field


class Vote(BaseModel):
    post_id: int = Field(title="ID of the post", examples=["1"])
    dir: Annotated[
        int,
        Field(
            ge=0,
            le=1,
            title="Vote direction",
            description="Indicates the direction of the vote. Use 1 for an upvote and 0 for a downvote.",  # noqa: E501
            examples=[0, 1],
        ),
    ]
