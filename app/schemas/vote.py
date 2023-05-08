from pydantic import BaseModel, Field, conint


class Vote(BaseModel):
    post_id: int = Field(title="ID of the post", example="1")
    dir: conint(ge=0, le=1) = Field(  # type: ignore
        title="Vote direction",
        description="Indicates the direction of the vote. Use 1 for an upvote and 0 for a downvote.",  # noqa: E501
        example=1,
    )
