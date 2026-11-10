import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.oauth import create_access_token
from app.models import Post, User, Vote


def _get_vote(session: Session, post_id: int, user_id: int) -> Vote | None:
    stmt = select(Vote).where(Vote.post_id == post_id, Vote.user_id == user_id)
    return session.execute(stmt).scalars().first()


# Fixture: Create an upvote for the first post and test user
@pytest.fixture()
def test_vote(test_posts: list[Post], session: Session, test_user: User) -> Vote:
    new_vote = Vote(post_id=test_posts[0].id, user_id=test_user.id, direction=1)
    session.add(new_vote)
    session.commit()
    return new_vote


# Test: Upvote a post should return 200 and persist direction=1
def test_upvote_post(
    authorized_client: TestClient,
    test_posts: list[Post],
    test_user: User,
    session: Session,
) -> None:
    post_id = test_posts[0].id
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": 1}
    )
    logging.debug(res.json())

    assert res.status_code == 200
    assert res.json() == {"message": "Vote registered"}
    vote = _get_vote(session, post_id, test_user.id)
    assert vote is not None
    assert vote.direction == 1


# Test: Downvote a post should return 200 and persist direction=-1
def test_downvote_post(
    authorized_client: TestClient,
    test_posts: list[Post],
    test_user: User,
    session: Session,
) -> None:
    post_id = test_posts[0].id
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": -1}
    )
    logging.debug(res.json())

    assert res.status_code == 200
    assert res.json() == {"message": "Vote registered"}
    vote = _get_vote(session, post_id, test_user.id)
    assert vote is not None
    assert vote.direction == -1


# Test: Changing an existing vote should update the same row
@pytest.mark.usefixtures("test_vote")
def test_change_vote_direction(
    authorized_client: TestClient,
    test_posts: list[Post],
    session: Session,
) -> None:
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "direction": -1}
    )
    logging.debug(res.json())

    assert res.status_code == 200
    assert res.json() == {"message": "Vote registered"}
    votes = session.execute(select(Vote)).scalars().all()
    assert len(votes) == 1
    assert votes[0].direction == -1


# Test: Repeating the same vote is idempotent and returns 200
@pytest.mark.parametrize("direction", [1, -1])
def test_vote_is_idempotent(
    authorized_client: TestClient,
    test_posts: list[Post],
    session: Session,
    direction: int,
) -> None:
    payload = {"post_id": test_posts[0].id, "direction": direction}

    first_res = authorized_client.post("/api/v1/votes/", json=payload)
    second_res = authorized_client.post("/api/v1/votes/", json=payload)

    assert first_res.status_code == 200
    assert second_res.status_code == 200
    votes = session.execute(select(Vote)).scalars().all()
    assert len(votes) == 1
    assert votes[0].direction == direction


# Test: Removing an existing vote should return 200 and delete the row
@pytest.mark.usefixtures("test_vote")
def test_remove_vote(
    authorized_client: TestClient,
    test_posts: list[Post],
    test_user: User,
    session: Session,
) -> None:
    post_id = test_posts[0].id
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": 0}
    )
    logging.debug(res.json())

    assert res.status_code == 200
    assert res.json() == {"message": "Vote removed"}
    assert _get_vote(session, post_id, test_user.id) is None


# Test: Removing a non-existent vote is idempotent and returns 200
def test_remove_vote_when_not_voted(
    authorized_client: TestClient, test_posts: list[Post], session: Session
) -> None:
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "direction": 0}
    )
    logging.debug(res.json())

    assert res.status_code == 200
    assert res.json() == {"message": "Vote removed"}
    assert session.execute(select(Vote)).scalars().all() == []


# Test: Voting on a non-existent post should return 404
def test_vote_post_non_exist(authorized_client: TestClient) -> None:
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": 9999999, "direction": 1}
    )
    logging.debug(res.json())

    assert res.status_code == 404
    assert res.json()["detail"] == "Post not found"


# Test: An unpublished post is not visible to other users
def test_vote_unpublished_post_from_other_user(
    authorized_client: TestClient, test_posts: list[Post], session: Session
) -> None:
    test_posts[2].published = False
    session.commit()

    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[2].id, "direction": 1}
    )
    logging.debug(res.json())

    assert res.status_code == 404
    assert res.json()["detail"] == "Post not found"


# Test: Owners cannot vote on their own unpublished posts
def test_vote_unpublished_own_post(
    authorized_client: TestClient, test_posts: list[Post], session: Session
) -> None:
    test_posts[0].published = False
    session.commit()

    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "direction": 1}
    )
    logging.debug(res.json())

    assert res.status_code == 404
    assert res.json()["detail"] == "Post not found"


# Test: Unauthorized user should not be able to vote
def test_vote_unauthorized_user(client: TestClient, test_posts: list[Post]) -> None:
    res = client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "direction": 1}
    )
    logging.debug(res.json())

    assert res.status_code == 401


# Test: Direction outside -1..1 should return 422
@pytest.mark.parametrize("direction", [-2, 2])
def test_vote_invalid_direction(
    authorized_client: TestClient, test_posts: list[Post], direction: int
) -> None:
    res = authorized_client.post(
        "/api/v1/votes/", json={"post_id": test_posts[0].id, "direction": direction}
    )
    logging.debug(res.json())

    assert res.status_code == 422


# Test: Post vote count is the sum of directions
def test_vote_count_uses_direction(
    authorized_client: TestClient,
    test_posts: list[Post],
    test_user2: User,
) -> None:
    post_id = test_posts[0].id

    upvote = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": 1}
    )
    assert upvote.status_code == 200

    other_token = create_access_token({"sub": test_user2.id})
    authorized_client.headers["Authorization"] = f"Bearer {other_token}"

    upvote = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": 1}
    )
    assert upvote.status_code == 200
    post = authorized_client.get(f"/api/v1/posts/{post_id}").json()
    assert post["votes"] == 2

    downvote = authorized_client.post(
        "/api/v1/votes/", json={"post_id": post_id, "direction": -1}
    )
    assert downvote.status_code == 200
    post = authorized_client.get(f"/api/v1/posts/{post_id}").json()
    assert post["votes"] == 0
