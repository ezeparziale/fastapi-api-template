import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.database import get_db
from app.models import Post, Vote
from app.schemas import Message, MessageDetail
from app.schemas import Vote as VoteSchema

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Vote created",
            "model": Message,
            "content": {
                "application/json": {"example": {"message": "Successfully added vote"}}
            },
        },
        204: {
            "description": "Vote deleted",
        },
        401: {
            "description": "Unauthorized",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Authorization required"}}
            },
        },
        404: {
            "description": "Post or Vote not found",
            "model": Message,
            "content": {
                "application/json": {
                    "examples": {
                        "post_not_found": {
                            "summary": "Post not found",
                            "value": {"detail": "Post not found"},
                        },
                        "vote_not_found": {
                            "summary": "Vote not found",
                            "value": {"detail": "Vote not found"},
                        },
                    }
                }
            },
        },
        409: {
            "description": "Post already voted",
            "model": MessageDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Post already voted by user"}
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Internal Server Error"}}
            },
        },
    },
)
def vote_post(
    vote: VoteSchema,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> Any:
    """
    ### Vote a post
    """
    try:
        stmt_select = select(Post).where(Post.id == vote.post_id)
        post = db.execute(stmt_select).scalars().first()

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found",
            )

        stmt_select_vote = select(Vote).where(
            Vote.post_id == vote.post_id, Vote.user_id == current_user.id
        )

        found_vote = db.execute(stmt_select_vote).scalars().first()

        if vote.dir == 1:
            if found_vote:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Post already voted by user",
                )
            new_vote = Vote(post_id=vote.post_id, user_id=current_user.id)
            db.add(new_vote)
            db.commit()
            return {"message": "Successfully added vote"}
        else:
            if not found_vote:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Vote does not exist"
                )

            stmt_delete_vote = (
                delete(Vote)
                .where(Vote.post_id == vote.post_id, Vote.user_id == current_user.id)
                .execution_options(synchronize_session=False)
            )
            db.execute(stmt_delete_vote)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
            )
    except Exception as e:
        logging.error(f"Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        )
