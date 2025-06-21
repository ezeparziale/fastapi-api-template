import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Post, User, Vote


# Fixture: Create a vote for the first post and test user
@pytest.fixture()
def test_vote(test_posts: list[Post], session: Session, test_user: User):
    new_vote = Vote(post_id=test_posts[0].id, user_id=test_user["id"])
    session.add(new_vote)
    session.commit()


# Test: Voting on a post should return 201
def test_votes_on_post(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1}
    )
    print(res.json())
    assert res.status_code == 201


# Test: Voting twice on the same post should return 409
def test_vote_twice_post(
    authorized_client: TestClient, test_posts: list[Post], test_vote: None
):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1}
    )
    print(res.json())
    assert res.status_code == 409


# Test: Deleting a vote should return 204
def test_delete_vote(
    authorized_client: TestClient, test_posts: list[Post], test_vote: None
):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 0}
    )
    assert res.status_code == 204


# Test: Deleting a non-existent vote should return 404
def test_delete_vote_non_exist(authorized_client: TestClient, test_posts: list[Post]):
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 0}
    )
    print(res.json())
    assert res.status_code == 404


# Test: Voting on a non-existent post should return 404
def test_vote_post_non_exist(authorized_client: TestClient):
    res = authorized_client.post("/api/v1/votes/", json={"post_id": 9999999, "dir": 0})
    print(res.json())
    assert res.status_code == 404


# Test: Unauthorized user should not be able to vote
def test_vote_unauthorized_user(client: TestClient, test_posts: list[Post]):
    res = client.post("/api/v1/votes/", json={"post_id": test_posts[0].id, "dir": 1})
    print(res.json())
    assert res.status_code == 401
