import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, UserCreditCard


# Test: GET /credit-card/ without authorization should return 401
def test_get_credit_card_unauthorized(client: TestClient) -> None:
    response = client.get("/api/v1/credit-card/")
    assert response.status_code == 401


# Test: PUT /credit-card/ without authorization should return 401
def test_update_credit_card_unauthorized(client: TestClient) -> None:
    payload = {
        "card_number": "4111111111111111",
        "expiration_date": "2030-12-31",
    }
    response = client.put("/api/v1/credit-card/", json=payload)
    assert response.status_code == 401


# Test: DELETE /credit-card/ without authorization should return 401
def test_delete_credit_card_unauthorized(client: TestClient) -> None:
    response = client.delete("/api/v1/credit-card/")
    assert response.status_code == 401


# Test: GET /credit-card/ when no credit card exists should return 404
def test_get_credit_card_not_found(authorized_client: TestClient) -> None:
    response = authorized_client.get("/api/v1/credit-card/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Credit card not found"


# Test: PUT /credit-card/ to create and update a credit card, then GET to verify
def test_update_and_get_credit_card(authorized_client: TestClient) -> None:
    payload = {
        "card_number": "4111111111111111",
        "expiration_date": "2030-12-31",
    }
    # Create (PUT)
    response = authorized_client.put("/api/v1/credit-card/", json=payload)
    assert response.status_code == 200
    assert response.json()["detail"] == "Credit card updated"

    # Retrieve (GET)
    response = authorized_client.get("/api/v1/credit-card/")
    assert response.status_code == 200
    data = response.json()
    # The card_number should be masked in the output
    assert data["card_number"] == "**** **** **** 1111"
    assert data["expiration_date"] == "2030-12-31"

    # Update (PUT) with a different card number and expiration date
    payload2 = {
        "card_number": "5555666677778888",
        "expiration_date": "2031-01-01",
    }
    response = authorized_client.put("/api/v1/credit-card/", json=payload2)
    assert response.status_code == 200
    assert response.json()["detail"] == "Credit card updated"

    # Verify update
    response = authorized_client.get("/api/v1/credit-card/")
    assert response.status_code == 200
    data = response.json()
    assert data["card_number"] == "**** **** **** 8888"
    assert data["expiration_date"] == "2031-01-01"


# Test: Repeated PUTs are idempotent and keep a single credit card per user
def test_update_credit_card_is_idempotent(
    authorized_client: TestClient, test_user: User, session: Session
) -> None:
    payload = {
        "card_number": "4111111111111111",
        "expiration_date": "2030-12-31",
    }
    for _ in range(2):
        response = authorized_client.put("/api/v1/credit-card/", json=payload)
        assert response.status_code == 200

    count = session.query(UserCreditCard).filter_by(user_id=test_user.id).count()
    assert count == 1


# Test: The database rejects a second credit card for the same user
def test_credit_card_is_unique_per_user(
    authorized_client: TestClient, test_user: User, session: Session
) -> None:
    payload = {
        "card_number": "4111111111111111",
        "expiration_date": "2030-12-31",
    }
    response = authorized_client.put("/api/v1/credit-card/", json=payload)
    assert response.status_code == 200

    session.add(UserCreditCard(user_id=test_user.id, credit_card=payload))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


# Test: DELETE /credit-card/ to remove the credit card, then GET to verify deletion
def test_delete_credit_card(authorized_client: TestClient) -> None:
    payload = {
        "card_number": "4111111111111111",
        "expiration_date": "2030-12-31",
    }
    # Create credit card
    authorized_client.put("/api/v1/credit-card/", json=payload)

    # Delete credit card
    response = authorized_client.delete("/api/v1/credit-card/")
    assert response.status_code == 204

    # Verify it no longer exists
    response = authorized_client.get("/api/v1/credit-card/")
    assert response.status_code == 404


# Test: DELETE /credit-card/ when no credit card exists should return 404
def test_delete_credit_card_not_found(authorized_client: TestClient) -> None:
    response = authorized_client.delete("/api/v1/credit-card/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Credit card not found"
