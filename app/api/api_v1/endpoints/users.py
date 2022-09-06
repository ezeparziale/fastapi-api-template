from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.oauth import get_current_user
from app.db.database import get_db
from app.models import User
from app.schemas import UserCreate, UserOut
from app.utils import get_password_hash

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> Any:
    """
    ### Create user
    """
    if db.query(User).filter_by(email=user.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This username already exists!",
        )
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/me", response_model=UserOut)
def get_user_me(current_user: User = Depends(get_current_user)) -> Any:
    """
    ### Get current user info
    """
    return current_user


@router.get("/{id}", response_model=UserOut)
def get_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    ### Get user by id
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with: {id} does not exists",
        )
    return user
