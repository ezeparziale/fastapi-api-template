from typing import Annotated

from fastapi import Depends, Query, Request
from pydantic import BaseModel

from app.core.oauth import get_current_user
from app.models import User
from app.services.cache import CacheService


async def get_cache_service(request: Request) -> CacheService:
    """
    Dependency to provide a CacheService instance.
    Captures the route template (e.g., /api/v1/posts/{id}) to handle selective caching.
    """
    route = request.scope.get("route")
    route_path = route.path if route else request.url.path
    return CacheService(endpoint_path=route_path)


CurrentUser = Annotated[User, Depends(get_current_user)]
CacheDep = Annotated[CacheService, Depends(get_cache_service)]


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
