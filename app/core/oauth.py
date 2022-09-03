from authlib.integrations.starlette_client import OAuth
from app.core.config import settings

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=settings.GOOGLE_CONF_URL,
    client_kwargs={
        "scope": settings.GOOGLE_SCOPES
    }
)
