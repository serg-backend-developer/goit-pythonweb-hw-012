import pytest

from sqlalchemy import select
from unittest.mock import Mock, AsyncMock

from src.database.models import User
from src.utils import constants
from tests.conftest import TestingSessionLocal


account_info = {
    "username": "username",
    "email": "username@gmail.com",
    "password": "testpassword",
    "role": "user",
}

unique_email_account = {
    "username": "username",
    "email": "username@gmail.com",
    "password": "12345678",
    "role": "user",
}

unique_account_data = {
    "username": "username2",
    "email": "username2@gmail.com",
    "password": "12345678",
    "role": "user",
}


def test_signup(client, monkeypatch):
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == account_info["username"]
    assert data["email"] == account_info["email"]
    assert "hashed_password" not in data
    assert "avatar" in data
    assert data["role"] == account_info["role"]


def test_register_with_existing_email(client, monkeypatch):
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == constants.USER_EMAIL_ALREADY_EXISTS


def test_register_with_existing_username(client, monkeypatch):
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=unique_email_account)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == constants.USER_NAME_ALREADY_EXISTS


def test_register_with_duplicate_email(client, monkeypatch):
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == constants.USER_EMAIL_ALREADY_EXISTS


def test_login_with_unconfirmed_account(client):
    response = client.post(
        "api/auth/login",
        data={
            "username": account_info.get("username"),
            "password": account_info.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.USER_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == account_info.get("email"))
        )
        user = user.scalar_one_or_none()
        if user:
            user.is_confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": account_info.get("username"),
            "password": account_info.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_login_with_wrong_password(client):
    response = client.post(
        "api/auth/login",
        data={"username": account_info.get("username"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.INVALID_CREDENTIALS


def test_login_with_wrong_username(client):
    response = client.post(
        "api/auth/login",
        data={"username": "username", "password": account_info.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.INVALID_CREDENTIALS


def test_login_with_validation_error(client):
    response = client.post(
        "api/auth/login", data={"password": account_info.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_confirm_email(client, monkeypatch):
    async_mock = AsyncMock(return_value="test@test.com")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    mock = Mock()
    mock.get_user_by_email = AsyncMock(return_value=Mock(is_confirmed=False))
    mock.confirmed_email = AsyncMock(return_value=True)
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/confirmed_email/token")
    assert response.status_code == 200
    assert response.json()["message"] == constants.EMAIL_CONFIRMED
    async_mock.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("test@test.com")
    mock.confirmed_email.assert_called_once_with("test@test.com")


@pytest.mark.asyncio
async def test_email_already_confirmed(client, monkeypatch):
    async_mock = AsyncMock(return_value="test@test.com")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    mock = Mock()
    mock.get_user_by_email = AsyncMock(return_value=Mock(is_confirmed=True))
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/confirmed_email/token")
    assert response.status_code == 200
    assert response.json()["message"] == constants.EMAIL_ALREADY_CONFIRMED
    async_mock.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("test@test.com")
    mock.confirmed_email.assert_not_called()


@pytest.mark.asyncio
async def test_request_email(client, monkeypatch):
    async_mock = AsyncMock()
    monkeypatch.setattr("src.api.auth.send_email", async_mock)
    client.post("api/auth/register", json=unique_account_data)
    response = client.post(
        "api/auth/request_email", json={"email": unique_account_data["email"]}
    )
    assert response.status_code == 200
    assert response.json()["message"] == constants.CHECK_YOUR_EMAIL


@pytest.mark.asyncio
async def test_request_email_already_confirmed(client, monkeypatch):
    async_mock = AsyncMock()
    monkeypatch.setattr("src.api.auth.send_email", async_mock)
    response = client.post("api/auth/request_email", json={"email": account_info["email"]})
    assert response.status_code == 200
    assert response.json()["message"] == constants.EMAIL_ALREADY_CONFIRMED


@pytest.mark.asyncio
async def test_confirm_update_password(client, monkeypatch):
    async_mock = AsyncMock(return_value="test@test.com")
    mock_from_token = AsyncMock(return_value="new_hashed_password")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    monkeypatch.setattr(
        "src.services.auth.get_password_from_token", mock_from_token
    )
    mock = Mock()
    mock.get_user_by_email = AsyncMock(
        return_value=Mock(id=1, email="test@test.com")
    )
    mock.update_password = AsyncMock(
        return_value=None
    )
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/update_password/token")
    assert response.status_code == 200
    assert response.json()["message"] == constants.PASSWORD_CHANGED
    async_mock.assert_called_once_with("token")
    mock_from_token.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("test@test.com")
    mock.update_password.assert_called_once_with(1, "new_hashed_password")


@pytest.mark.asyncio
async def test_update_password_invalid_or_expired_token(client, monkeypatch):
    async_mock = AsyncMock(return_value=None)
    mock_get_password_from_token = AsyncMock(return_value=None)
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    monkeypatch.setattr(
        "src.services.auth.get_password_from_token", mock_get_password_from_token
    )
    response = client.get("api/auth/update_password/token")
    assert response.status_code == 400
    assert response.json()["detail"] == constants.INVALID_OR_EXPIRED_TOKEN
    async_mock.assert_called_once_with("token")
    mock_get_password_from_token.assert_called_once_with("token")


@pytest.mark.asyncio
async def test_update_password_user_not_found(client, monkeypatch):
    async_mock = AsyncMock(return_value="test@test.com")
    mock_get_password_from_token = AsyncMock(return_value="new_hashed_password")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    monkeypatch.setattr(
        "src.services.auth.get_password_from_token", mock_get_password_from_token
    )
    mock = Mock()
    mock.get_user_by_email = AsyncMock(return_value=None)
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/update_password/token")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"
    async_mock.assert_called_once_with("token")
    mock_get_password_from_token.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("ttest@test.com")