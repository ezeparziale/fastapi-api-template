from typing import Annotated

from fastapi import Depends, Query

from app.core.oauth import get_current_user
from app.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]


class CommonQueryParams:
    def __init__(
        self,
        offset: Annotated[int, Query(description="Offset for pagination", ge=0)] = 0,
        limit: Annotated[int, Query(description="Limit for pagination", gt=0)] = 10,
        search: Annotated[str | None, Query(description="Search")] = None,
        sort: Annotated[
            str | None,
            Query(
                description="Sort",
                examples={
                    "empty": {
                        "description": "Sort by default",
                        "value": "",
                    },
                    "asc": {
                        "description": "Sort by asc",
                        "value": "id",
                    },
                    "desc": {
                        "description": "Sort by asc",
                        "value": "-id",
                    },
                    "mutiple fields": {
                        "description": "Sort by multiple fields",
                        "value": "field_1,-field_2",
                    },
                },
            ),
        ] = None,
    ):
        self.offset = offset
        self.limit = limit
        self.search = search
        self.sort = sort


CommonsDep = Annotated[CommonQueryParams, Depends(CommonQueryParams)]
