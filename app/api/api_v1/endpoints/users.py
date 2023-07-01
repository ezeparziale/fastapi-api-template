from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from loguru import logger
from sqlalchemy import String, cast, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.default_responses import default_responses
from app.api.deps import CommonsDep, CurrentUser
from app.db.database import get_db
from app.models import User
from app.schemas import MessageDetail, UserCreate, UserOut
from app.utils import get_password_hash

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        **default_responses,
        201: {
            "description": "User created",
            "model": UserOut,
        },
        409: {
            "description": "User already exists",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "User already exists"}}
            },
        },
    },
)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """
    ### Create user
    """
    # Check if user exists
    stmt_select = select(User).filter_by(email=user.email)
    user_exists = db.execute(stmt_select).scalars().first()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    # Create user
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": UserOut,
        },
    },
)
def get_user_me(
    current_user: CurrentUser,
) -> UserOut:
    """
    ### Get current user info
    """
    return current_user  # type: ignore


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": UserOut,
        },
        404: {
            "description": "User not found",
            "model": MessageDetail,
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
def get_user(
    id: Annotated[int, Path(description="The ID of the user to get")],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> UserOut:
    """
    ### Get user by id
    """
    # Get user
    stmt_select = select(User).where(User.id == id).limit(1)
    user = db.execute(stmt_select).scalars().first()

    # Check if user not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": list[UserOut],
        },
        400: {
            "description": "Bad request",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Invalid sort field"}}
            },
        },
    },
)
def get_users(
    response: Response,
    commons: CommonsDep,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """
    ### Get users list
    """
    # Query
    stmt_select = select(User)

    # Search
    if commons.search:
        stmt_select = stmt_select.where(
            or_(
                cast(User.id, String).ilike(commons.search),
                User.email.icontains(commons.search),
            )
        )

    # Total rows filtered
    total_row_filtered = (
        db.execute(select(func.count()).select_from(stmt_select.subquery()))
        .scalars()
        .one()
    )

    # Sort
    try:
        if commons.sort:
            fields = commons.sort.split(",")
            for field in fields:
                if field.startswith("-"):
                    stmt_select = stmt_select.order_by(desc(getattr(User, field[1:])))
                else:
                    stmt_select = stmt_select.order_by(getattr(User, field))
        else:
            stmt_select = stmt_select.order_by(User.id)
    except Exception as e:
        logger.warning(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field"
        ) from e

    # Pagination
    stmt_select = stmt_select.limit(commons.limit).offset(commons.offset)

    # Get data
    users = db.execute(stmt_select).scalars().all()

    # Total rows
    total_rows = db.execute(select(func.count(User.id))).scalars().one()

    # Extra headers
    response.headers["Total-Count"] = str(total_rows)
    response.headers["Total-Count-Filtered"] = str(total_row_filtered)
    response.headers["Pagination-Pages"] = str(ceil(total_rows / commons.limit))

    return users  # type: ignore[return-value]
