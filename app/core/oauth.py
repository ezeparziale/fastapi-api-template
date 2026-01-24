from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast

from authlib.integrations.starlette_client import OAuth
from authlib.jose import jwt
from authlib.jose.errors import JoseError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.database import get_db
from app.models import User
from app.schemas import TokenData

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth = OAuth()

oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url=settings.GOOGLE_CONF_URL,
    client_kwargs={"scope": settings.GOOGLE_SCOPES},
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        payload=to_encode, key=SECRET_KEY, header={"alg": ALGORITHM}
    )
    return cast(bytes, encoded_jwt).decode("utf-8")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY)
        payload.validate()
        sub: int | None = payload.get("sub", None)
        if sub is None:
            raise credentials_exception
        token_data = TokenData(id=sub)
    except (JoseError, ValidationError) as exc:
        raise credentials_exception from exc

    stmt_select = select(User).where(User.id == token_data.id)
    user = db.execute(stmt_select).scalars().first()
    if user is None:
        raise credentials_exception
    return user
