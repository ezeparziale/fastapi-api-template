from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel

from app.core.oauth import get_current_user
from app.models import User

CurrentUser = Annotated[User, Depends(get_current_user)]


class CommonFilterParams(BaseModel):
    offset: int = Query(0, description="Offset for pagination", ge=0)
    limit: int = Query(100, description="Limit for pagination", ge=1, le=1000)
    search: str | None = Query(None, description="Search")
    sort_by: str | None = Query(
        None,
        description="Sort",
        openapi_examples={
            "default": {
                "summary": "Default sort",
                "description": (
                    "Applies no specific sort order."
                    "Results will be returned in the order they were originally retrieved or stored."  # noqa: E501
                ),
                "value": "",
            },
            "asc": {
                "summary": "Ascending order",
                "description": "Sorts the results in ascending order based on the specified field.",  # noqa: E501
                "value": "id",
            },
            "desc": {
                "summary": "Descending order",
                "description": (
                    "Sorts the results in descending order based on the specified field."  # noqa: E501
                    "The symbol '-' is used before the field name to indicate descending order."  # noqa: E501
                ),
                "value": "-id",
            },
            "multiple fields": {
                "summary": "Multiple fields sorting",
                "description": (
                    "Sorts the results based on multiple fields."
                    "Separate field names by commas, and use '-' before a field name to specify descending order for that field."  # noqa: E501
                ),
                "value": "field_1,-field_2",
            },
        },
    )


FilterParams = Annotated[CommonFilterParams, Query()]
