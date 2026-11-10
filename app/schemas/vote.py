from typing import Annotated

from pydantic import BaseModel, Field


class VoteIn(BaseModel):
    post_id: int = Field(title="ID of the post", examples=["1"])
    direction: Annotated[
        int,
        Field(
            ge=-1,
            le=1,
            title="Vote direction",
            description="Use 1 to upvote, -1 to downvote and 0 to remove your vote.",  # noqa: E501
            examples=[-1, 0, 1],
        ),
    ]
