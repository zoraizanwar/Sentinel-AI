"""Automated Tests for Authentication & Profile Endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthentication:

    async def test_user_registration_success(self, async_client: AsyncClient):
        payload = {
            "email": "analyst@sentinel.local",
            "password": "SecretPassword123",
            "full_name": "Senior Fraud Analyst",
            "organization_name": "Acme Global Risk"
        }
        res = await async_client.post("/api/v1/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["email"] == "analyst@sentinel.local"
        assert data["full_name"] == "Senior Fraud Analyst"
        assert "default_organization_id" in data

    async def test_duplicate_registration_fails(self, async_client: AsyncClient):
        payload = {
            "email": "duplicate@sentinel.local",
            "password": "Password123",
            "full_name": "Test User",
            "organization_name": "Test Org"
        }
        res1 = await async_client.post("/api/v1/auth/register", json=payload)
        assert res1.status_code == 201

        res2 = await async_client.post("/api/v1/auth/register", json=payload)
        assert res2.status_code == 400
        assert res2.json()["error_code"] == "EMAIL_ALREADY_EXISTS"

    async def test_user_login_flow(self, async_client: AsyncClient):
        # Register
        reg_payload = {
            "email": "login_test@sentinel.local",
            "password": "ValidPassword999",
            "full_name": "Login User",
            "organization_name": "Login Org"
        }
        await async_client.post("/api/v1/auth/register", json=reg_payload)

        # Login with correct password
        login_res = await async_client.post("/api/v1/auth/login", json={
            "email": "login_test@sentinel.local",
            "password": "ValidPassword999"
        })
        assert login_res.status_code == 200
        token_data = login_res.json()
        assert "access_token" in token_data

        # Login with incorrect password
        bad_login_res = await async_client.post("/api/v1/auth/login", json={
            "email": "login_test@sentinel.local",
            "password": "WrongPassword"
        })
        assert bad_login_res.status_code == 401

    async def test_current_user_profile(self, async_client: AsyncClient):
        reg_payload = {
            "email": "profile_user@sentinel.local",
            "password": "ProfilePassword123",
            "full_name": "Profile User",
            "organization_name": "Profile Corp"
        }
        reg_res = await async_client.post("/api/v1/auth/register", json=reg_payload)
        token = reg_res.json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        me_res = await async_client.get("/api/v1/auth/me", headers=headers)
        assert me_res.status_code == 200
        user_data = me_res.json()
        assert user_data["email"] == "profile_user@sentinel.local"
        assert len(user_data["memberships"]) == 1
        assert user_data["memberships"][0]["role"] == "ORGANIZATION_ADMIN"
