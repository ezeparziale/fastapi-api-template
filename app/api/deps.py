from typing import Annotated

from fastapi import Depends

from app.core.oauth import get_current_user
from app.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]


class CommonQueryParams:
    def __init__(self, offset: int = 0, limit: int = 10, search: str | None = ""):
        self.offset = offset
        self.limit = limit
        self.search = search


CommonsDep = Annotated[CommonQueryParams, Depends(CommonQueryParams)]
