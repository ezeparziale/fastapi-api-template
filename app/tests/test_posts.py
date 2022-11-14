import pytest

from app.schemas import Post as PostSchema
from app.schemas import PostOUT


def test_get_all_posts(authorized_client, test_posts):
    res = authorized_client.get("/api/v1/posts/")

    def validate(post):
        return PostOUT(**post)

    post_map = map(validate, res.json())
    print(res.json())

    assert len(res.json()) == len(test_posts)
    assert res.status_code == 200


def test_unauthorized_user_get_all_posts(client, test_posts):
    res = client.get("/api/v1/posts/")
    print(res.json())
    assert res.status_code == 401


def test_unauthorized_user_get_one_posts(client, test_posts):
    res = client.get(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_get_one_post_non_exist(authorized_client, test_posts):
    res = authorized_client.get("/api/v1/posts/999999999999")
    print(res.json())
    assert res.status_code == 404


def test_get_one_post(authorized_client, test_posts):
    res = authorized_client.get(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    post = PostOUT(**res.json())
    print(post)
    assert post.Post.id == test_posts[0].id
    assert res.status_code == 200


@pytest.mark.parametrize(
    "title, content, published",
    [("Titulo1", "Contenido1", True), ("Titulo2", "Contenido2", False)],
)
def test_create_post(
    authorized_client, test_user, test_posts, title, content, published
):
    res = authorized_client.post(
        "/api/v1/posts/",
        json={"title": title, "content": content, "published": published},
    )

    print(res.json())
    created_post = PostSchema(**res.json())

    assert res.status_code == 201
    assert created_post.title == title
    assert created_post.content == content
    assert created_post.published == published
    assert created_post.owner_id == test_user["id"]


def test_create_post_default_published_true(authorized_client, test_user, test_posts):
    res = authorized_client.post(
        "/api/v1/posts/", json={"title": "asd", "content": "qwe"}
    )

    print(res.json())
    created_post = PostSchema(**res.json())

    assert res.status_code == 201
    assert created_post.title == "asd"
    assert created_post.content == "qwe"
    assert created_post.published is True
    assert created_post.owner_id == test_user["id"]


def test_unauthorized_create_post(client, test_user, test_posts):
    res = client.post("/api/v1/posts/", json={"title": "asd", "content": "qwe"})
    print(res.json())
    assert res.status_code == 401


def test_unauthorized_delete_post(client, test_user, test_posts):
    res = client.delete(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_delete_post_success(authorized_client, test_user, test_posts):
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[0].id}")
    print(res)
    assert res.status_code == 204


def test_delete_post_non_exists(authorized_client, test_user, test_posts):
    res = authorized_client.delete("v/posts/9999999999")
    print(res)
    assert res.status_code == 404


def test_delete_other_user_post(authorized_client, test_user, test_posts):
    res = authorized_client.delete(f"/api/v1/posts/{test_posts[2].id}")
    print(res)
    assert res.status_code == 403


def test_update_post(authorized_client, test_user, test_posts):
    data = {"title": "new title", "content": "new content", "id": test_posts[0].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[0].id}", json=data)
    print(res)
    updated_post = PostSchema(**res.json())
    print(updated_post)
    assert res.status_code == 200
    assert updated_post.title == data["title"]
    assert updated_post.content == data["content"]


def test_update_other_user_post(authorized_client, test_user, test_user2, test_posts):
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put(f"/api/v1/posts/{test_posts[2].id}", json=data)
    print(res)
    assert res.status_code == 403


def test_unauthorized_update_post(client, test_user, test_posts):
    res = client.put(f"/api/v1/posts/{test_posts[0].id}")
    print(res.json())
    assert res.status_code == 401


def test_update_post_non_exists(authorized_client, test_user, test_posts):
    data = {"title": "new title", "content": "new content", "id": test_posts[2].id}
    res = authorized_client.put("/api/v1/posts/9999999999", json=data)
    print(res)
    assert res.status_code == 404
