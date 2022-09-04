from fastapi import APIRouter, Request, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.core.oauth import oauth, create_access_token
from app.schemas import Token
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from app.utils import utils

auth_router = APIRouter()


@auth_router.get("/login_google")
async def login_google(request: Request):
    """
    ### Login Google
    """
    redirect_uri = request.url_for("authorize")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_router.get("/authorize")
async def authorize(request: Request, db: Session = Depends(get_db)):
    """
    ### Authorize
    """
    token = await oauth.google.authorize_access_token(request)
    user = db.query(User).filter(User.email == token["userinfo"]["email"]).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/login", response_model=Token)
def login(
    user_credentials: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == user_credentials.username)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    if not utils.verify(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )

    access_token = create_access_token(data={"user_id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}