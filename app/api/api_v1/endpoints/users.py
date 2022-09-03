from fastapi import APIRouter, status, Depends, HTTPException
from app.schemas import UserCreate, UserOut
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """ 
    ### Create user
    """
    return {"id": 1}


@router.get("/{id}", response_model=UserOut)
def get_user(id: int, db: Session = Depends(get_db)):
    """
    ### Get user
    """
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with: {id} does not exists",
        )
    return user