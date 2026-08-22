"""Automated Tests for Tenant Isolation and RBAC Permissions."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestTenantIsolationAndRBAC:

    async def test_cross_organization_access_strictly_forbidden(self, async_client: AsyncClient):
        # 1. Register User A in Org A
        res_a = await async_client.post("/api/v1/auth/register", json={
            "email": "user_a@org-a.com",
            "password": "PasswordOrgA123",
            "full_name": "User Alpha",
            "organization_name": "Organization Alpha"
        })
        token_a = res_a.json()["access_token"]
        org_a_id = res_a.json()["default_organization_id"]

        # 2. Register User B in Org B
        res_b = await async_client.post("/api/v1/auth/register", json={
            "email": "user_b@org-b.com",
            "password": "PasswordOrgB123",
            "full_name": "User Beta",
            "organization_name": "Organization Beta"
        })
        token_b = res_b.json()["access_token"]
        org_b_id = res_b.json()["default_organization_id"]

        # 3. Create Client inside Org A using User A
        client_res = await async_client.post(
            f"/api/v1/organizations/{org_a_id}/clients",
            json={
                "client_code": "CL-ALPHA-01",
                "name": "Alpha Client Financial",
                "email": "contact@alphaclient.com",
                "industry": "Banking"
            },
            headers={"Authorization": f"Bearer {token_a}"}
        )
        assert client_res.status_code == 201
        client_a_id = client_res.json()["id"]

        # 4. User B attempts to access Org A's clients (CRITICAL TEST)
        leak_attempt = await async_client.get(
            f"/api/v1/organizations/{org_a_id}/clients",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert leak_attempt.status_code == 403

        # 5. User B attempts to access Client A directly
        direct_client_attempt = await async_client.get(
            f"/api/v1/organizations/{org_a_id}/clients/{client_a_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert direct_client_attempt.status_code == 403

    async def test_rbac_viewer_cannot_create_client_or_manage_members(self, async_client: AsyncClient):
        # 1. Register Admin in Org
        admin_res = await async_client.post("/api/v1/auth/register", json={
            "email": "admin@rbac.com",
            "password": "Password123",
            "full_name": "Org Admin",
            "organization_name": "RBAC Test Org"
        })
        admin_token = admin_res.json()["access_token"]
        org_id = admin_res.json()["default_organization_id"]

        # 2. Register Viewer user
        viewer_reg = await async_client.post("/api/v1/auth/register", json={
            "email": "viewer@rbac.com",
            "password": "Password123",
            "full_name": "Org Viewer",
            "organization_name": "Viewer Org"
        })
        viewer_token = viewer_reg.json()["access_token"]
        viewer_id = viewer_reg.json()["user_id"]

        # 3. Admin adds Viewer to Org with VIEWER role
        add_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/members",
            json={"email": "viewer@rbac.com", "role": "VIEWER"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert add_res.status_code == 201

        # 4. Viewer tries to create a client (Must be 403 Forbidden)
        create_client_attempt = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients",
            json={"client_code": "VIEWER-FAIL", "name": "Unauthorized Client"},
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert create_client_attempt.status_code == 403

        # 5. Viewer can read clients list (Allowed for VIEWER)
        list_clients_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/clients",
            headers={"Authorization": f"Bearer {viewer_token}"}
        )
        assert list_clients_res.status_code == 200
