import asyncio
import json
from typing import Any, cast

from fastapi.testclient import TestClient

from app.main import app, handle_500_errors


def test_handle_500_errors_returns_json_response() -> None:
    response = asyncio.run(handle_500_errors(cast(Any, None), RuntimeError("boom")))

    assert response.status_code == 500
    assert json.loads(bytes(response.body)) == {"detail": "Internal Server Error"}


def test_root_redirects_to_docs() -> None:
    with TestClient(app) as client:
        res = client.get("/", follow_redirects=False)

    assert res.status_code in (302, 307)
    assert res.headers["location"] == "/docs"
