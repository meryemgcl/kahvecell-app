from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)


def verified_customer(db):
    user = User(
        phone_number="05339876543",
        full_name="KahveCell Test",
        email="test@example.com",
        password_hash=hash_password("Ankara123!"),
        role=UserRole.CUSTOMER,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def access_token(client: TestClient, db):
    user = verified_customer(db)
    login = client.post(
        "/api/v1/auth/login",
        json={"phone_number": user.phone_number, "password": "Ankara123!"},
    )
    assert login.status_code == 200
    return login.json()["access_token"]


def auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_subscription_plans_are_listed(client: TestClient):
    response = client.get("/api/v1/subscriptions/plans")
    assert response.status_code == 200
    plans = {plan["plan_type"]: plan for plan in response.json()}
    assert plans["STARTER"]["monthly_price"] == 89.99
    assert plans["STARTER"]["monthly_credits"] == 10
    assert plans["PREMIUM"]["monthly_credits"] == 20
    assert plans["UNLIMITED"]["monthly_credits"] == -1


def test_successful_card_creates_active_subscription(client: TestClient, db):
    token = access_token(client, db)
    response = client.post(
        "/api/v1/subscriptions",
        headers=auth_headers(token),
        json={
            "plan_type": "STARTER",
            "card_token": "4242-4242-4242-4242",
        },
    )
    assert response.status_code == 200
    assert response.json()["plan_type"] == "STARTER"
    assert response.json()["remaining_credits"] == 10
    assert response.json()["status"] == "ACTIVE"


def test_failed_card_does_not_create_subscription(client: TestClient, db):
    token = access_token(client, db)
    response = client.post(
        "/api/v1/subscriptions",
        headers=auth_headers(token),
        json={
            "plan_type": "PREMIUM",
            "card_token": "4000-0000-0000-0002",
        },
    )
    assert response.status_code == 402
    assert "FAILED" in str(response.json())
