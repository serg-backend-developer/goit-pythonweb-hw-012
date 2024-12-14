import pytest

from fastapi import HTTPException, status
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from src.utils import constants


admin = {
    "id": 1,
    "username": "agent007",
    "email": "agent007@gmail.com",
    "password": "12345678",
    "role": "admin",
    "is_confirmed": True,
    "avatar": "https://example.com/avatar.png",
}


@pytest.mark.asyncio
async def test_me(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": admin["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=admin)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    response = client.get("/api/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == admin["email"]
    assert response.json()["username"] == admin["username"]
    mock_jwt.assert_called_once()
    mock_from_db.assert_called_once_with(admin["username"], mock.ANY)


@pytest.mark.asyncio
async def test_me_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.get("/api/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"