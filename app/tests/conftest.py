import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.oauth import create_access_token
from app.db.database import Base, get_db
from app.main import app
from app.models import Post

SQLALCHEMY_DATABASE_URL = f"{settings.SQLALCHEMY_DATABASE_URI}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)


@pytest.fixture
def test_user(client):
    user_data = {"email": "abc1@test.com", "password": "abc123"}
    res = client.post("/api/v1/users/", json=user_data)
    assert res.status_code == 201
    print(res.json())
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def test_user2(client):
    user_data = {"email": "abc2@test.com", "password": "abc123"}
    res = client.post("/api/v1/users/", json=user_data)
    assert res.status_code == 201
    print(res.json())
    new_user = res.json()
    new_user["password"] = user_data["password"]
    return new_user


@pytest.fixture
def token(test_user):
    return create_access_token({"id": test_user["id"]})


@pytest.fixture
def authorized_client(client, token):
    client.headers = {**client.headers, "Authorization": f"Bearer {token}"}
    return client


@pytest.fixture
def test_posts(test_user, test_user2, session):
    posts_data = [
        {"title": "Title_1", "content": "Content_1", "owner_id": test_user["id"]},
        {"title": "Title_2", "content": "Content_2", "owner_id": test_user["id"]},
        {"title": "Title_2", "content": "Content_2", "owner_id": test_user2["id"]},
    ]

    def create_user_model(post):
        return Post(**post)

    post_map = map(create_user_model, posts_data)
    posts = list(post_map)
    session.add_all(posts)
    session.commit()
    post = session.query(Post).all()
    return post
