import pytest
from fastapi.testclient import TestClient

from app.models import Post, User
from app.schemas import NewPostOut, PostOut, PostUpdateOut


def test_get_all_posts(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.get("/api/v1/posts/")

    def validate(post):
        return PostOut(**post)

    map(validate, res.json())
    print(res.json())

    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200


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
):
    params = {"sort_by": fields}
    res = authorized_client.get("/api/v1/posts", params=params)
    print(res.json())
    assert res.status_code == status_code


def test_get_posts_search(authorized_client: TestClient, test_posts: list[Post]):
    params = {"search": test_posts[0].title}
    res = authorized_client.get("/api/v1/posts", params=params)
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    print(data)
    assert data[0]["Post"]["title"] == test_posts[0].title


def test_get_posts_search_no_posts(
    authorized_client: TestClient, test_posts: list[Post]
):
    params = {"search": "xxxx"}
    res = authorized_client.get("/api/v1/posts", params=params)
    print(res.json())
    assert res.status_code == 200
    data = res.json()
    print(data)
    assert len(data) == 0


def test_unauthorized_user_get_all_posts(client: TestClient):
    res = client.get("/api/v1/posts/")
    print(res.json())
    assert res.status_code == 401


def test_unauthorized_user_get_one_posts(client: TestClient, test_posts: list[Post]):
    res = client.get(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_get_one_post_non_exist(authorized_client: TestClient):
    res = authorized_client.get("/api/v1/posts/999999999999")
    print(res.json())
    assert res.status_code == 404


def test_get_one_post(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.get(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    post = PostOut(**res.json())
    print(post)
    assert post.Post.id == test_posts[0].id
    assert res.status_code == 200


@pytest.mark.parametrize(
    "title, content, published",
    [("Titulo1", "Contenido1", True), ("Titulo2", "Contenido2", False)],
)
def test_create_post(
    authorized_client: TestClient,
    test_user: User,
    title: str,
    content: str,
    published: bool,
):
    res = authorized_client.post(
        "/api/v1/posts/",
        json={"title": title, "content": content, "published": published},
    )

    print(res.json())
    created_post = NewPostOut(**res.json())

    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.content == content
    assert created_post.published == published
    assert created_post.owner_id == test_user["id"]


def test_create_post_default_published_true(
    authorized_client: TestClient, test_user: User
):
    res = authorized_client.post(
        "/api/v1/posts/", json={"title": "asd", "content": "qwe"}
    )

    print(res.json())
    created_post = NewPostOut(**res.json())

    assert res.status_code == 201
    assert created_post.title == "asd"
    assert created_post.content == "qwe"
    assert created_post.published is True
    assert created_post.owner_id == test_user["id"]


def test_unauthorized_create_post(client: TestClient):
    res = client.post("/api/v1/posts/", json={"title": "asd", "content": "qwe"})
    print(res.json())
    assert res.status_code == 401


def test_unauthorized_delete_post(client: TestClient, test_posts: list[Post]):
    res = client.delete(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_delete_post_success(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[0].id}")
    print(res)
    assert res.status_code == 204


def test_delete_post_non_exists(authorized_client: TestClient):
    res = authorized_client.delete("/api/v1/posts/9999999999")
    print(res)
    assert res.status_code == 404


def test_delete_other_user_post(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[2].id}")
    print(res)
    assert res.status_code == 403


def test_update_post(authorized_client: TestClient, test_posts: list[Post]):
    data = {"title": "new title", "content": "new content", "id": test_posts[0].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[0].id}", json=data)
    print(res)
    updated_post = PostUpdateOut(**res.json())
    print(updated_post)
    assert res.status_code == 200
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]


def test_update_other_user_post(authorized_client: TestClient, test_posts: list[Post]):
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[2].id}", json=data)
    print(res)
    assert res.status_code == 403


def test_unauthorized_update_post(client: TestClient, test_posts: list[Post]):
    res = client.put(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_update_post_non_exists(authorized_client: TestClient, test_posts: list[Post]):
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put("/api/v1/posts/9999999999", json=data)
    print(res)
    assert res.status_code == 404
