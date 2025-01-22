from typing import Annotated, Any

from pydantic import AnyHttpUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    # FastAPI
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FastAPI Google Auth Login"
    SUMMARY: str = "A flexible FastAPI template for building robust and scalable APIs."
    DESCRIPTION: str = (
        "**🚀 A versatile FastAPI template** designed to kickstart your API development.\n\n"  # noqa: E501
        "### ✨ Key Features\n"
        "- 🔒 **Authentication**: Secure user login and token management.\n"
        "- 👤 **User Management**: Create, update, and manage user profiles.\n"
        "- 📦 **CRUD Operations**: Simplify resource management with built-in CRUD functionality.\n"  # noqa: E501
        "- ⚙️ **Customizable Endpoints**: Adapt the template to fit your project needs.\n\n"  # noqa: E501
        "This template is **ideal for building scalable and maintainable APIs** "
        "whether you're working on a blog, e-commerce platform, or any other application. 🛠️"  # noqa: E501
    )

    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyHttpUrl] | str, BeforeValidator(parse_cors)
    ] = []

    # Jwt
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Google
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_SCOPES: str = "openid email profile"
    GOOGLE_CONF_URL: str = (
        "https://accounts.google.com/.well-known/openid-configuration"
    )

    # Database
    POSTGRES_HOSTNAME: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOSTNAME,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Encryption key for db fields
    ENCRYPTION_KEY: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # pyright: ignore
