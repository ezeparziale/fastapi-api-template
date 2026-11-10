from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.default_responses import default_responses
from app.api.deps import CacheDep, CurrentUser
from app.db.database import get_db
from app.models import Post, Vote
from app.schemas import Message, MessageDetail, VoteIn

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=Message,
    responses={
        **default_responses,
        200: {
            "description": "Vote registered or removed",
            "model": Message,
            "content": {
                "application/json": {
                    "examples": {
                        "registered": {
                            "summary": "Vote registered",
                            "value": {"message": "Vote registered"},
                        },
                        "removed": {
                            "summary": "Vote removed",
                            "value": {"message": "Vote removed"},
                        },
                    }
                }
            },
        },
        404: {
            "description": "Post not found",
            "model": MessageDetail,
            "content": {"application/json": {"example": {"detail": "Post not found"}}},
        },
    },
)
async def vote_post(
    vote: VoteIn,
    current_user: CurrentUser,
    background_tasks: BackgroundTasks,
    cache: CacheDep,
    db: Session = Depends(get_db),
) -> Message:
    """
    ### Vote a post

    Use `direction=1` to upvote, `-1` to downvote or `0` to remove your vote.
    Sending the same direction again has no additional effect, and `0` without
    an existing vote leaves the post unchanged.

    Only published posts can be voted on.
    """
    # Get post
    stmt_select = select(Post).where(Post.id == vote.post_id)
    post = db.execute(stmt_select).scalars().first()

    # Check if post exists and is published
    if not post or not post.published:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if vote.direction == 0:
        stmt_delete_vote = (
            delete(Vote)
            .where(Vote.post_id == vote.post_id, Vote.user_id == current_user.id)
            .execution_options(synchronize_session=False)
        )
        db.execute(stmt_delete_vote)
        message = "Vote removed"
    else:
        stmt_upsert_vote = (
            insert(Vote)
            .values(
                post_id=vote.post_id,
                user_id=current_user.id,
                direction=vote.direction,
            )
            .on_conflict_do_update(
                index_elements=[Vote.user_id, Vote.post_id],
                set_={"direction": vote.direction, "updated_at": func.now()},
            )
        )
        db.execute(stmt_upsert_vote)
        message = "Vote registered"

    db.commit()

    # The vote count is baked into the cached post and posts list
    background_tasks.add_task(cache.delete, f"posts:{vote.post_id}")
    background_tasks.add_task(cache.clear_pattern, "posts:all:*")

    return Message(message=message)
