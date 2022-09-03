from fastapi import APIRouter, Request

from app.core.oauth import oauth

auth_router = APIRouter()


@auth_router.get("/login")
async def login(request: Request):
    """
    ### Login
    """
    redirect_uri = request.url_for("authorize")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_router.get("/authorize")
async def authorize(request: Request):
    """
    ### Authorize
    """
    token = await oauth.google.authorize_access_token(request)
    return token
