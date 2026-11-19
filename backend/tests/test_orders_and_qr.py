from datetime import datetime, timedelta, UTC

from fastapi.testclient import TestClient

from app.api.v1.shops import haversine_distance
from app.core.qr import create_qr_payload, verify_qr_payload
from app.core.security import hash_password
from app.models import (
    Product,
    Shop,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    User,
    UserRole,
)


def create_customer(db):
    user = User(
        phone_number="05339876543",
        full_name="Siparis Test",
        email="siparis@example.com",
        password_hash=hash_password("Ankara123!"),
        role=UserRole.CUSTOMER,
        is_verified=True,
    )
    subscription = Subscription(
        plan_type=SubscriptionPlan.STARTER,
        remaining_credits=3,
        status=SubscriptionStatus.ACTIVE,
        started_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    user.subscriptions.append(subscription)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_shop_and_product(db):
    shop = Shop(
        name="KahveCell Kızılay",
        address="Kızılay Meydanı, Çankaya, Ankara",
        latitude=39.9208,
        longitude=32.8541,
        opening_hours={"weekdays": "08:00-23:00"},
        rating=4.6,
        is_active=True,
    )
    db.add(shop)
    db.flush()
    product = Product(
        shop_id=shop.id,
        name="Espresso",
        description="Yoğun espresso",
        price=55.00,
        is_available=True,
        category="hot",
    )
    db.add(product)
    db.commit()
    db.refresh(shop)
    db.refresh(product)
    return shop, product


def login(client: TestClient, db):
    user = create_customer(db)
    response = client.post(
        "/api/v1/auth/login",
        json={"phone_number": user.phone_number, "password": "Ankara123!"},
    )
    assert response.status_code == 200
    return user, {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_order_creation_deducts_credit(client: TestClient, db):
    user, headers = login(client, db)
    shop, product = create_shop_and_product(db)
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id
    ).first()
    before = subscription.remaining_credits

    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "shop_id": shop.id,
            "product_id": product.id,
            "customizations": {"size": "M", "extra_shot": True},
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "PENDING"
    db.expire_all()
    updated = db.query(Subscription).filter(
        Subscription.user_id == user.id
    ).first()
    assert updated.remaining_credits == before - 1


def test_haversine_distance_is_calculated():
    distance = haversine_distance(39.9208, 32.8541, 39.9208, 32.8541)
    assert distance == 0

    distance = haversine_distance(39.9208, 32.8541, 39.8916, 32.8662)
    assert 3.0 < distance < 4.0


def test_hmac_qr_signature_is_valid_and_tamper_is_rejected():
    payload, payload_json, qr_data_url = create_qr_payload(
        "order-id",
        "user-id",
        "shop-id",
        "2026-11-19T20:00:00",
    )
    assert payload_json
    assert qr_data_url.startswith("data:image/png;base64")
    assert verify_qr_payload(payload) is True

    payload["shop_id"] = "changed-shop-id"
    assert verify_qr_payload(payload) is False
