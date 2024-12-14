import pytest

from fastapi import HTTPException, status
from unittest.mock import AsyncMock, MagicMock

from src.schemas.contacts import ContactModel
from src.utils import constants

account_info = {
    "id": 1,
    "username": "username",
    "email": "username@gmail.com",
    "password": "testpassword",
    "role": "user",
    "is_confirmed": True,
}

contacts = [
    {
        "id": 1,
        "firstname": "Sergii",
        "lastname": "Shevchenko",
        "birthday": "1991-08-24",
        "email": "serg@gmail.com",
        "phonenumber": "0123456789",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "info": "Test",
    },
    {
        "id": 2,
        "firstname": "Petr",
        "lastname": "Ivanov",
        "birthday": "1999-01-01",
        "email": "pert@gmail.com",
        "phonenumber": "9876543210",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
        "info": None,
    },
]

payload = {
    "firstname": "Sergii",
    "lastname": "Shevchenko",
    "birthday": "1991-08-24",
    "email": "serg@gmail.com",
    "phonenumber": "0123456789",
}


@pytest.mark.asyncio
async def test_fetch_upcoming_birthdays(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    async_mock = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", async_mock
    )
    mock_birthdays = AsyncMock(return_value=contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_upcoming_birthdays",
        mock_birthdays,
    )
    response = client.get("/api/contacts/birthdays?days=7", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(contacts)
    assert response.json()[0]["firstname"] == contacts[0]["firstname"]
    mock_birthdays.assert_called_once_with(7, account_info)


@pytest.mark.asyncio
async def test_fetch_upcoming_birthdays_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.get("/api/contacts/birthdays?days=7")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_fetch_contacts_without_filters(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    async_mock = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", async_mock
    )
    mock_contacts = AsyncMock(return_value=contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )
    response = client.get("/api/contacts/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(contacts)
    assert response.json()[0]["email"] == contacts[0]["email"]
    mock_contacts.assert_called_once_with("", "", "", 0, 100, account_info)


@pytest.mark.asyncio
async def test_fetch_contacts_with_filters(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    mock_contacts = AsyncMock(return_value=contacts[0])
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )
    response = client.get(
        "/api/contacts/?firstname=Sergii&lastname=Shevchenko", headers=auth_headers
    )
    assert response.status_code == 200
    assert len(response.json()) == len(contacts[0])
    assert response.json()[0]["firstname"] == "Sergii"
    mock_contacts.assert_called_once_with("Sergii", "Shevchenko", "", 0, 100, account_info)


@pytest.mark.asyncio
async def test_fetch_contacts_pagination(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    contacts = [
        {
            "id": 3,
            "firstname": "Test",
            "lastname": "Test",
            "email": "test@test.com",
            "phonenumber": "1122334455",
            "birthday": "1991-01-01",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
    ]
    mock_contacts = AsyncMock(return_value=contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )
    response = client.get("/api/contacts/?skip=2&limit=1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(contacts)
    assert response.json()[0]["id"] == 3
    mock_contacts.assert_called_once_with("", "", "", 2, 1, account_info)


@pytest.mark.asyncio
async def test_fetch_contacts_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.get("/api/contacts/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_fetch_contact(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    contact = contacts[0]
    mock_contact = AsyncMock(return_value=contact)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contact_by_id", mock_contact
    )
    response = client.get("/api/contacts/1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == contact["id"]
    assert response.json()["firstname"] == contact["firstname"]
    mock_contact.assert_called_once_with(1, account_info)


@pytest.mark.asyncio
async def test_fetch_contact_not_found(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    mock_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contact_by_id", mock_contact
    )
    response = client.get("/api/contacts/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_contact.assert_called_once_with(999, account_info)


@pytest.mark.asyncio
async def test_fetch_contact_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.get("/api/contacts/1")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_new_contact(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    contact = contacts[0]
    mock_create_contact = AsyncMock(return_value=contact)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.create_new_contact",
        mock_create_contact,
    )
    response = client.post("/api/contacts/", json=payload, headers=auth_headers)
    contact_model = ContactModel(**payload)
    assert response.status_code == 201
    assert response.json()["id"] == contact["id"]
    assert response.json()["firstname"] == contact["firstname"]
    mock_create_contact.assert_called_once_with(contact_model, account_info)


@pytest.mark.asyncio
async def test_create_contact_with_incorrect_data(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    incorrect_payload = {
        "firstname": "",
    }
    response = client.post("/api/contacts/", json=incorrect_payload, headers=auth_headers)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_new_contact_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.post("/api/contacts/", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_contact(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    updated_contact = {
        **contacts[0],
        "firstname": "NewTest",
        "lastname": "NewTest",
    }
    mock_update_contact = AsyncMock(return_value=updated_contact)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.update_exist_contact",
        mock_update_contact,
    )
    payload = {
        "firstname": "NewTest",
        "lastname": "NewTest",
        "birthday": "1991-08-24",
        "email": "serg@gmail.com",
        "phonenumber": "0123456789",
    }
    contact_id = contacts[0]["id"]
    response = client.put(
        f"/api/contacts/{contact_id}", json=payload, headers=auth_headers
    )
    contact_model = ContactModel(**payload)
    assert response.status_code == 200
    assert response.json()["id"] == updated_contact["id"]
    assert response.json()["firstname"] == updated_contact["firstname"]
    assert response.json()["lastname"] == updated_contact["lastname"]
    mock_update_contact.assert_called_once_with(contact_id, contact_model, account_info)


@pytest.mark.asyncio
async def test_update_contact_not_found(client, monkeypatch, auth_headers):
    mock_jwt_decode = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt_decode)
    mock_get_user_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_get_user_from_db
    )
    mock_update_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.update_exist_contact",
        mock_update_contact,
    )
    payload = {
        "firstname": "tt",
        "lastname": "hh",
        "birthday": "1991-08-24",
        "email": "incorrect@example.com",
        "phonenumber": "0123456789",
    }
    response = client.put("/api/contacts/999", json=payload, headers=auth_headers)
    contact_model = ContactModel(**payload)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_update_contact.assert_called_once_with(999, contact_model, account_info)


@pytest.mark.asyncio
async def test_update_contact_with_incorrect_data(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    invalid_payload = {
        "firstname": "",
    }
    response = client.put("/api/contacts/1", json=invalid_payload, headers=auth_headers)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_update_contact_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    response = client.put("/api/contacts/1", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_contact(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    mock_delete_contact = AsyncMock(return_value=contacts[0])
    monkeypatch.setattr(
        "src.services.contacts.ContactService.delete_contact",
        mock_delete_contact,
    )
    contact_id = contacts[0]["id"]
    response = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == contacts[0]
    mock_delete_contact.assert_called_once_with(contact_id, account_info)


@pytest.mark.asyncio
async def test_delete_contact_not_found(client, monkeypatch, auth_headers):
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr(
        "src.services.auth.get_user_from_db", mock_from_db
    )
    mock_delete_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.delete_contact",
        mock_delete_contact,
    )
    contact_id = 999
    response = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_delete_contact.assert_called_once_with(contact_id, account_info)


@pytest.mark.asyncio
async def test_delete_contact_unauthenticated(client, monkeypatch):
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr(
        "src.services.auth.get_current_user", mock
    )
    contact_id = contacts[0]["id"]
    response = client.delete(f"/api/contacts/{contact_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"