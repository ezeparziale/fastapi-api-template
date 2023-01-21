from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.oauth import get_current_user
from app.db.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.utils import get_password_hash

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """
    ### Create user
    """
    stmt_select = select(User).filter_by(email=user.email)
    user_exists = db.execute(stmt_select).scalars().first()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username already exists!",
        )

    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me")
def get_user_me(current_user: User = Depends(get_current_user)) -> UserOut:
    """
    ### Get current user info
    """
    return current_user


@router.get("/{id}")
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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


@router.get("/")
def get_users(
    db: Session = Depends(get_db),
    current_user: int = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0,
    search: str | None = "",
) -> list[UserOut]:
    """
    ### Get all users info
    """
    stmt_select = (
        select(User).where(User.email.contains(search)).limit(limit).offset(offset)
    )
    users = db.execute(stmt_select).scalars().all()

    return users
