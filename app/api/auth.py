from fastapi import APIRouter, Request, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import User
from app.core.oauth import oauth, create_access_token

auth_router = APIRouter()


@auth_router.get("/login")
async def login(request: Request):
    """
    ### Login
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
