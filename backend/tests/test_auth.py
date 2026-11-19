from fastapi.testclient import TestClient


def register_user(client: TestClient, phone: str = "05339876543"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "phone_number": phone,
            "full_name": "KahveCell Test",
            "email": "test@example.com",
            "password": "Ankara123!",
        },
    )


def test_gsm_registration_and_otp_verification(client: TestClient):
    register_response = register_user(client)
    assert register_response.status_code == 200
    assert register_response.json()["success"] is True
    assert "1234" in register_response.json()["message"]

    verify_response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "05339876543", "code": "1234"},
    )
    assert verify_response.status_code == 200
    tokens = verify_response.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]


def test_login_returns_jwt_and_me_endpoint(client: TestClient):
    assert register_user(client).status_code == 200
    verified = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "05339876543", "code": "1234"},
    )
    assert verified.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"phone_number": "05339876543", "password": "Ankara123!"},
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]

    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["phone_number"] == "05339876543"
    assert me_response.json()["role"] == "CUSTOMER"


def test_invalid_otp_is_rejected(client: TestClient):
    assert register_user(client).status_code == 200
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"phone_number": "05339876543", "code": "1111"},
    )
    assert response.status_code == 400
    assert "hatalı" in response.json()["detail"].lower()
