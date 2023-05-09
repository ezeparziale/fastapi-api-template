from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.orm import Session

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
        201: {
            "description": "User created",
            "model": UserOut,
        },
        401: {
            "description": "Unauthorized",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Authorization required"}}
            },
        },
        409: {
            "description": "User already exists",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "User already exists"}}
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
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """
    ### Create user
    """
    stmt_select = select(User).filter_by(email=user.email)
    user_exists = db.execute(stmt_select).scalars().first()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", status_code=status.HTTP_200_OK)
def get_user_me(
    current_user: CurrentUser = None,  # type: ignore
) -> UserOut:
    """
    ### Get current user info
    """
    return current_user


@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_user(
    id: Annotated[int, Path(description="The ID of the user to get")],
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
) -> UserOut:
    """
    ### Get user by id
    """
    stmt_select = select(User).where(User.id == id).limit(1)
    user = db.execute(stmt_select).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with: {id} does not exists",
        )
    return user


@router.get("/", status_code=status.HTTP_200_OK)
def get_users(
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,  # type: ignore
    commons: CommonsDep = None,  # type: ignore
) -> list[UserOut]:
    """
    ### Get all users info
    """
    stmt_select = (
        select(User)
        .where(User.email.contains(commons.search))
        .limit(commons.limit)
        .offset(commons.offset)
    )
    users = db.execute(stmt_select).scalars().all()

    return users  # type: ignore[return-value]
