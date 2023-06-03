from math import ceil
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Response, status
from sqlalchemy import delete, desc, func, select, update
from sqlalchemy.orm import Session

from app.api.default_responses import default_responses
from app.api.deps import CommonsDep, CurrentUser
from app.db.database import get_db
from app.models import Post, Vote
from app.schemas import (
    MessageDetail,
    NewPostOut,
    PostCreateIn,
    PostOut,
    PostUpdateIn,
    PostUpdateOut,
)

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "List of posts",
            "model": list[PostOut],
        },
    },
)
def get_posts(
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
    commons: CommonsDep = None,  # type: ignore
    response: Response = None,  # type: ignore
) -> list[PostOut]:
    """
    ### Get post list
    """
    # Query
    stmt_select = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .group_by(Post.id)
    )

    # Search
    if commons.search:
        stmt_select = stmt_select.where(Post.title.contains(commons.search))

    # Total rows filtered
    total_row_filtered = (
        db.execute(select(func.count()).select_from(stmt_select)).scalars().one()
    )

    # Sort
    if commons.sort:
        fields = commons.sort.split(",")
        for field in fields:
            if field.startswith("-"):
                stmt_select = stmt_select.order_by(desc(getattr(Post, field[1:])))
            else:
                stmt_select = stmt_select.order_by(getattr(Post, field))
    else:
        stmt_select = stmt_select.order_by(Post.id)

    # Pagination
    stmt_select = stmt_select.limit(commons.limit).offset(commons.offset)

    # Get data
    posts = db.execute(stmt_select).all()

    # Total rows
    total_rows = db.execute(select(func.count(Post.id))).scalars().one()

    # Extra headers
    response.headers["Total-Count"] = str(total_rows)
    response.headers["Total-Count-Filtered"] = str(total_row_filtered)
    response.headers["Pagination-Pages"] = str(ceil(total_rows / commons.limit))

    return posts  # type: ignore[return-value]


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        **default_responses,
        201: {
            "description": "Post created",
            "model": NewPostOut,
        },
    },
)
def create_posts(
    post: Annotated[PostCreateIn, Body(description="Post info")],
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> NewPostOut:
    """
    ### Create post
    """
    new_post = Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "Post info",
            "model": PostOut,
        },
        404: {
            "description": "Post not found",
            "model": MessageDetail,
            "content": {"application/json": {"example": {"detail": "Post not found"}}},
        },
    },
)
def get_post(
    id: Annotated[int, Path(description="The ID of the post to get")],
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> PostOut:
    """
    ### Get post by id
    """
    stmt_select = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .group_by(Post.id)
        .where(Post.id == id)
        .limit(1)
    )
    post = db.execute(stmt_select).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )
    return post  # type: ignore[return-value]


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        **default_responses,
        204: {
            "description": "Post deleted",
        },
        403: {
            "description": "Forbidden",
            "model": MessageDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized to perform requested action"}
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
def delete_post(
    id: Annotated[int, Path(description="The ID of the post to delete")],
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> None:
    """
    ### Delete post
    """
    stmt_select = select(Post).where(Post.id == id).limit(1)
    post_query = db.execute(stmt_select)

    post = post_query.scalars().first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    stmt_delete = (
        delete(Post).where(Post.id == id).execution_options(synchronize_session=False)
    )
    db.execute(stmt_delete)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # type: ignore[return-value] # noqa: E501


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "Post updated",
            "model": PostUpdateOut,
        },
        403: {
            "description": "Forbidden",
            "model": MessageDetail,
            "content": {
                "application/json": {
                    "example": {"detail": "Not authorized to perform requested action"}
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
def update_post(
    id: Annotated[int, Path(description="The ID of the post to update")],
    post: Annotated[PostUpdateIn, Body(description="Post info to update")],
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> PostUpdateOut:
    """
    ### Update post
    """
    stmt_select = select(Post).where(Post.id == id).limit(1)
    post_to_update = db.execute(stmt_select).scalars().first()

    if post_to_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    if post_to_update.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    stmt_update = (
        update(Post)
        .where(Post.id == id)
        .values(post.dict())
        .execution_options(synchronize_session=False)
        .returning(Post)
    )
    result = db.scalars(stmt_update)
    db.commit()
    return result.first()  # type: ignore[return-value]
