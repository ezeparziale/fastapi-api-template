from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.api_v1.api import api_router
from app.core.config import settings

# FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)


# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)
