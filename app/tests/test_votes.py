import pytest

from app.models import Vote


@pytest.fixture()
def test_vote(test_posts, session, test_user):
    new_vote = Vote(post_id=test_posts[0].id, user_id=test_user["id"])
    session.add(new_vote)
    session.commit()


def test_votes_on_post(authorized_client, test_posts):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1}
    )
    print(res.json())
    assert res.status_code == 201


def test_vote_twice_post(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1}
    )
    print(res.json())
    assert res.status_code == 409


def test_delete_vote(authorized_client, test_posts, test_vote):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 0}
    )
    print(res.json())
    assert res.status_code == 201


def test_delete_vote_non_exist(authorized_client, test_posts):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 0}
    )
    print(res.json())
    assert res.status_code == 404


def test_vote_post_non_exist(authorized_client, test_posts):
    res = authorized_client.post("/api/v1/votes/", json={"post_id": 9999999, "dir": 0})
    print(res.json())
    assert res.status_code == 404


def test_vote_unauthorized_user(client, test_posts):
    res = client.post("/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1})
    print(res.json())
    assert res.status_code == 401
