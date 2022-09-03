from pydantic import BaseSettings

class Settings(BaseSettings):
    # FastAPI
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Google Auth Login"
    SECRET_KY: str

    # Google
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_SCOPES: str = "openid email profile"
    GOOGLE_CONF_URL: str = "https://accounts.google.com/.well-known/openid-configuration"

    class Config:
        env_file = ".env"

settings = Settings()