import logging
from typing import Any

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_cache_service
from app.core.config import settings
from app.core.oauth import create_access_token
from app.main import app
from app.models import Post, User
from app.schemas import NewPostOut, PostOut


class FakeCache:
    def __init__(self, get_value: Any = None) -> None:
        self.get_value = get_value

    async def get(self, key: str) -> Any:
        return self.get_value


@pytest.fixture(autouse=True)
def clear_posts_cache() -> None:
    redis_client = redis.Redis(
        host=settings.REDIS_HOSTNAME,
        port=settings.REDIS_PORT,
        socket_connect_timeout=settings.CACHE_CONNECT_TIMEOUT,
        socket_timeout=settings.CACHE_TIMEOUT,
    )
    try:
        keys = redis_client.keys("posts:*")
        if keys:
            redis_client.delete(*keys)
    except redis.RedisError:
        pass
    finally:
        redis_client.close()


# Test: Get all posts should return 200 and the correct number of posts
def test_get_all_posts(authorized_client: TestClient, test_posts: list[Post]) -> None:
    res = authorized_client.get("/api/v1/posts/")

    def validate(post: dict[str, Any]) -> PostOut:
        return PostOut(**post)

    data = res.json()
    [validate(item) for item in data]
    logging.debug(data)

    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200


# Test: Get posts sorted by various fields, including invalid ones
@pytest.mark.parametrize(
    "fields, status_code",
    [
        ("id", 200),
        ("-id", 200),
        ("title", 200),
        ("-title", 200),
        ("content", 200),
        ("-content", 200),
        ("published", 200),
        ("-published", 200),
        ("created_at", 200),
        ("-created_at", 200),
        ("updated_at", 200),
        ("-updated_at", 200),
        ("field_not_exists", 400),
        ("-field_not_exists", 400),
        ("id,title", 200),
        ("-id,title", 200),
    ],
)
def test_get_posts_sort_by_fields(
    authorized_client: TestClient, fields: str, status_code: int
) -> None:
    params = {"sort_by": fields}
    res = authorized_client.get("/api/v1/posts", params=params)
    logging.debug(res.json())
    assert res.status_code == status_code


# Test: Search posts by title should return the correct post
def test_get_posts_search(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    params = {"search": test_posts[0].title}
    res = authorized_client.get("/api/v1/posts", params=params)
    logging.debug(res.json())
    assert res.status_code == 200
    data = res.json()
    logging.debug(data)
    assert data[0]["title"] == test_posts[0].title


# Test: Search posts with no matching results should return empty list
@pytest.mark.usefixtures("test_posts")
def test_get_posts_search_no_posts(authorized_client: TestClient) -> None:
    params = {"search": "xxxx"}
    res = authorized_client.get("/api/v1/posts", params=params)
    logging.debug(res.json())
    assert res.status_code == 200
    data = res.json()
    logging.debug(data)
    assert len(data) == 0


# Test: Pagination pages are based on filtered results, not all posts
def test_get_posts_pagination_pages_uses_filtered_count(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    params: dict[str, str | int] = {"search": test_posts[0].title, "limit": 1}
    res = authorized_client.get("/api/v1/posts/", params=params)

    assert res.status_code == 200
    assert res.headers["Total-Count"] == str(len(test_posts))
    assert res.headers["Total-Count-Filtered"] == "1"
    assert res.headers["Pagination-Pages"] == "1"


# Test: Unauthorized user should not be able to get all posts
def test_unauthorized_user_get_all_posts(client: TestClient) -> None:
    res = client.get("/api/v1/posts/")
    logging.debug(res.json())
    assert res.status_code == 401


# Test: Unauthorized user should not be able to get a single post
def test_unauthorized_user_get_one_posts(
    client: TestClient, test_posts: list[Post]
) -> None:
    res = client.get(f"/api/v1/posts/{test_posts[0].id}")
    logging.debug(res.json())
    assert res.status_code == 401


# Test: Get a non-existent post should return 404
def test_get_one_post_non_exist(authorized_client: TestClient) -> None:
    res = authorized_client.get("/api/v1/posts/999999999")
    logging.debug(res.json())
    assert res.status_code == 404


# Test: Get a single post by id should return the correct post
def test_get_one_post(authorized_client: TestClient, test_posts: list[Post]) -> None:
    res = authorized_client.get(f"/api/v1/posts/{test_posts[0].id}")
    logging.debug(res.json())
    post = PostOut(**res.json())
    logging.debug(post)
    assert post.id == test_posts[0].id
    assert res.status_code == 200


# Test: Unpublished posts are hidden from other users in the list
def test_get_posts_hides_unpublished_from_other_users(
    authorized_client: TestClient, test_posts: list[Post], session: Session
) -> None:
    test_posts[2].published = False
    session.commit()

    res = authorized_client.get("/api/v1/posts/", params={"search": "Title_2"})

    assert res.status_code == 200
    assert [post["id"] for post in res.json()] == [test_posts[1].id]
    assert res.headers["Total-Count"] == "2"
    assert res.headers["Total-Count-Filtered"] == "1"


# Test: Owners can see their own unpublished posts in the list
def test_get_posts_shows_own_unpublished(
    authorized_client: TestClient, test_user: User, session: Session
) -> None:
    draft = Post(
        title="Owner draft",
        content="Draft content",
        published=False,
        owner_id=test_user.id,
    )
    session.add(draft)
    session.commit()
    session.refresh(draft)

    res = authorized_client.get("/api/v1/posts/", params={"search": "Owner draft"})

    assert res.status_code == 200
    assert [post["id"] for post in res.json()] == [draft.id]


# Test: List cache entries do not leak unpublished posts across users
def test_get_posts_unpublished_cache_is_scoped_per_user(
    authorized_client: TestClient,
    test_user: User,
    test_user2: User,
    session: Session,
) -> None:
    draft = Post(
        title="Scoped draft",
        content="Draft content",
        published=False,
        owner_id=test_user.id,
    )
    session.add(draft)
    session.commit()

    params = {"search": "Scoped draft"}
    owner_res = authorized_client.get("/api/v1/posts/", params=params)
    assert [post["id"] for post in owner_res.json()] == [draft.id]

    other_token = create_access_token({"sub": test_user2.id})
    authorized_client.headers["Authorization"] = f"Bearer {other_token}"
    other_res = authorized_client.get("/api/v1/posts/", params=params)

    assert other_res.status_code == 200
    assert other_res.json() == []


# Test: Unpublished posts are only visible to their owner by id
def test_get_unpublished_post_is_only_visible_to_owner(
    authorized_client: TestClient,
    test_user: User,
    test_user2: User,
    session: Session,
) -> None:
    draft = Post(
        title="Hidden post",
        content="Draft content",
        published=False,
        owner_id=test_user.id,
    )
    session.add(draft)
    session.commit()
    url = f"/api/v1/posts/{draft.id}"

    owner_res = authorized_client.get(url)
    assert owner_res.status_code == 200
    assert owner_res.json()["id"] == draft.id

    other_token = create_access_token({"sub": test_user2.id})
    authorized_client.headers["Authorization"] = f"Bearer {other_token}"
    other_res = authorized_client.get(url)

    assert other_res.status_code == 404


# Test: Create post with various data should return 201 and correct post data
@pytest.mark.parametrize(
    "title, content, published",
    [("Title1", "Content1", True), ("Title2", "Content2", False)],
)
def test_create_post(
    authorized_client: TestClient,
    test_user: User,
    title: str,
    content: str,
    published: bool,
) -> None:
    res = authorized_client.post(
        "/api/v1/posts/",
        json={"title": title, "content": content, "published": published},
    )

    logging.debug(res.json())
    created_post = NewPostOut(**res.json())

    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.content == content
    assert created_post.published == published
    assert created_post.owner_id == test_user.id


# Test: Create post without published field should default to True
def test_create_post_default_published_true(
    authorized_client: TestClient, test_user: User
) -> None:
    res = authorized_client.post(
        "/api/v1/posts/", json={"title": "asd", "content": "qwe"}
    )

    logging.debug(res.json())
    created_post = NewPostOut(**res.json())

    assert res.status_code == 201
    assert created_post.title == "asd"
    assert created_post.content == "qwe"
    assert created_post.published is True
    assert created_post.owner_id == test_user.id


# Test: Unauthorized user should not be able to create a post
def test_unauthorized_create_post(client: TestClient) -> None:
    res = client.post("/api/v1/posts/", json={"title": "asd", "content": "qwe"})
    logging.debug(res.json())
    assert res.status_code == 401


# Test: Unauthorized user should not be able to delete a post
def test_unauthorized_delete_post(client: TestClient, test_posts: list[Post]) -> None:
    res = client.delete(f"/api/v1/posts/{test_posts[0].id}")
    logging.debug(res.json())
    assert res.status_code == 401


# Test: Delete a post successfully should return 204
def test_delete_post_success(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[0].id}")
    logging.debug(res)
    assert res.status_code == 204


# Test: Delete a non-existent post should return 404
def test_delete_post_non_exists(authorized_client: TestClient) -> None:
    res = authorized_client.delete("/api/v1/posts/999999999")
    logging.debug(res)
    assert res.status_code == 404


# Test: User should not be able to delete another user's post (should return 403)
def test_delete_other_user_post(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[2].id}")
    logging.debug(res)
    assert res.status_code == 403


# Test: Update a post successfully should return 200 and updated data
def test_update_post(
    authorized_client: TestClient, test_user: User, test_posts: list[Post]
) -> None:
    data = {"title": "new title", "content": "new content", "id": test_posts[0].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[0].id}", json=data)
    logging.debug(res)
    updated_post = PostOut(**res.json())
    logging.debug(updated_post)
    assert res.status_code == 200
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]
    assert updated_post.id == test_posts[0].id
    assert updated_post.owner.id == test_user.id
    assert updated_post.votes == 0


# Test: User should not be able to update another user's post (should return 403)
def test_update_other_user_post(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[2].id}", json=data)
    logging.debug(res)
    assert res.status_code == 403


# Test: Unauthorized user should not be able to update a post
def test_unauthorized_update_post(client: TestClient, test_posts: list[Post]) -> None:
    res = client.put(f"/api/v1/posts/{test_posts[0].id}")
    logging.debug(res.json())
    assert res.status_code == 401


# Test: Update a non-existent post should return 404
def test_update_post_non_exists(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put("/api/v1/posts/999999999", json=data)
    logging.debug(res)
    assert res.status_code == 404


# Test: Patch a post with a single field should update only that field
@pytest.mark.parametrize(
    "field, value",
    [
        ("title", "patched title"),
        ("content", "patched content"),
        ("published", False),
    ],
)
def test_patch_post_single_field(
    authorized_client: TestClient,
    test_user: User,
    test_posts: list[Post],
    field: str,
    value: str | bool,
) -> None:
    original = test_posts[0]
    res = authorized_client.patch(f"/api/v1/posts/{original.id}", json={field: value})
    logging.debug(res.json())
    assert res.status_code == 200
    patched = PostOut(**res.json())
    assert getattr(patched, field) == value
    for other in ("title", "content", "published"):
        if other != field:
            assert getattr(patched, other) == getattr(original, other)
    assert patched.id == original.id
    assert patched.owner.id == test_user.id
    assert patched.votes == 0


# Test: Patch a post with an empty body should return 400
def test_patch_post_empty_body(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    res = authorized_client.patch(f"/api/v1/posts/{test_posts[0].id}", json={})
    logging.debug(res.json())
    assert res.status_code == 400
    assert res.json()["detail"] == "No fields to update"


# Test: Unauthorized user should not be able to patch a post
def test_patch_post_unauthorized(client: TestClient, test_posts: list[Post]) -> None:
    res = client.patch(f"/api/v1/posts/{test_posts[0].id}", json={"title": "x"})
    logging.debug(res.json())
    assert res.status_code == 401


# Test: User should not be able to patch another user's post (should return 403)
def test_patch_other_user_post(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    res = authorized_client.patch(
        f"/api/v1/posts/{test_posts[2].id}", json={"title": "x"}
    )
    logging.debug(res.json())
    assert res.status_code == 403


# Test: Patch a non-existent post should return 404
def test_patch_post_non_exists(authorized_client: TestClient) -> None:
    res = authorized_client.patch("/api/v1/posts/999999999", json={"title": "x"})
    logging.debug(res.json())
    assert res.status_code == 404


def test_get_all_posts_returns_cached_payload(authorized_client: TestClient) -> None:
    cached = {"headers": {"X-Cache": "HIT"}, "posts": []}
    app.dependency_overrides[get_cache_service] = lambda: FakeCache(cached)
    try:
        res = authorized_client.get("/api/v1/posts/")
    finally:
        app.dependency_overrides.pop(get_cache_service, None)

    assert res.status_code == 200
    assert res.json() == []
    assert res.headers["x-cache"] == "HIT"


def test_get_one_post_returns_cached_payload(
    authorized_client: TestClient, test_posts: list[Post]
) -> None:
    url = f"/api/v1/posts/{test_posts[0].id}"
    cached = authorized_client.get(url).json()

    app.dependency_overrides[get_cache_service] = lambda: FakeCache(cached)
    try:
        res = authorized_client.get(url)
    finally:
        app.dependency_overrides.pop(get_cache_service, None)

    assert res.status_code == 200
    assert res.json() == cached
