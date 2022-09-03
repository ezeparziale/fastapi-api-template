from fastapi import FastAPI

from app.api.api_v1.api import api_router
from app.api.auth import auth_router
from app.core.config import settings
from starlette.middleware.sessions import SessionMiddleware

# FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KY)


# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, tags=["authorization"])