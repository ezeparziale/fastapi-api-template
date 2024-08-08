from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.api_v1.api import api_router
from app.api.health import router as health_router
from app.core.config import settings
from app.middlewares import ProcessTimeHeaderMiddleware

from .logger import setup_logging

# FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Logger
setup_logging()

# Middlewares
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


app.add_middleware(ProcessTimeHeaderMiddleware)


@app.exception_handler(500)
async def handle_500_errors(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# Routes
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health_router, tags=["Health"])


@app.get("/", include_in_schema=False)
async def docs_redirect() -> RedirectResponse:
    return RedirectResponse(url="/docs")
