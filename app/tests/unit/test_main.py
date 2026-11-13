import asyncio
import json
from typing import Any, cast

from fastapi.testclient import TestClient
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.main import app, handle_500_errors


def _session_middleware_kwargs() -> dict[str, Any]:
    for middleware in app.user_middleware:
        if middleware.cls is cast(Any, SessionMiddleware):
            return middleware.kwargs
    raise AssertionError("SessionMiddleware is not registered")


def test_session_middleware_hardens_cookie_and_uses_separate_secret() -> None:
    kwargs = _session_middleware_kwargs()

    assert kwargs["secret_key"] == settings.SESSION_SECRET_KEY
    assert kwargs["secret_key"] != settings.SECRET_KEY
    assert kwargs["same_site"] == "lax"
    assert kwargs["https_only"] is (settings.ENVIRONMENT != "local")


def test_handle_500_errors_returns_json_response() -> None:
    response = asyncio.run(handle_500_errors(cast(Any, None), RuntimeError("boom")))

    assert response.status_code == 500
    assert json.loads(bytes(response.body)) == {"detail": "Internal Server Error"}


def test_root_redirects_to_docs() -> None:
    with TestClient(app) as client:
        res = client.get("/", follow_redirects=False)

    assert res.status_code in (302, 307)
    assert res.headers["location"] == "/docs"
