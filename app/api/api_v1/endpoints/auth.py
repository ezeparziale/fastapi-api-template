from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.oauth import create_access_token, oauth
from app.db.database import get_db
from app.models import User
from app.schemas import Token
from app.utils import normalize_email, verify_password

router = APIRouter()

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.get("/login/google")
async def login_google(request: Request) -> Any:
    """
    ### Login Google
    """
    redirect_uri = request.url_for("auth_via_google")
    return await oauth.google.authorize_redirect(request, str(redirect_uri))


@router.get("/google", response_model=Token)
async def auth_via_google(request: Request, db: Session = Depends(get_db)) -> Any:
    """
    ### Authorize
    """
    token = await oauth.google.authorize_access_token(request)
    email = normalize_email(token["userinfo"]["email"])
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise INVALID_CREDENTIALS

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    """
    ### Login user
    """
    email = normalize_email(user_credentials.username)
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise INVALID_CREDENTIALS

    if not verify_password(user_credentials.password, user.password):
        raise INVALID_CREDENTIALS

    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer"}
