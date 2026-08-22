"""Automated Tests for Client CRUD and Dataset Ingestion Persistence."""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestClientsAndDatasets:

    async def test_client_crud_lifecycle(self, async_client: AsyncClient):
        # Register user and org
        reg_res = await async_client.post("/api/v1/auth/register", json={
            "email": "manager@enterprise.local",
            "password": "Password123",
            "full_name": "Risk Manager",
            "organization_name": "Enterprise Risk Corp"
        })
        token = reg_res.json()["access_token"]
        org_id = reg_res.json()["default_organization_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Client
        create_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients",
            json={
                "client_code": "CL-FINTECH-01",
                "name": "Fintech Innovations Ltd",
                "email": "risk@fintech.com",
                "industry": "Payments"
            },
            headers=headers
        )
        assert create_res.status_code == 201
        client_data = create_res.json()
        client_id = client_data["id"]
        assert client_data["client_code"] == "CL-FINTECH-01"

        # 2. Update Client
        update_res = await async_client.put(
            f"/api/v1/organizations/{org_id}/clients/{client_id}",
            json={"name": "Fintech Global Payments"},
            headers=headers
        )
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Fintech Global Payments"

        # 3. Archive Client
        archive_res = await async_client.delete(
            f"/api/v1/organizations/{org_id}/clients/{client_id}",
            headers=headers
        )
        assert archive_res.status_code == 200
        assert archive_res.json()["status"] == "ARCHIVED"

    async def test_dataset_upload_and_validation(self, async_client: AsyncClient, sample_valid_df):
        reg_res = await async_client.post("/api/v1/auth/register", json={
            "email": "uploader@enterprise.local",
            "password": "Password123",
            "full_name": "Dataset Uploader",
            "organization_name": "Ingestion Corp"
        })
        token = reg_res.json()["access_token"]
        org_id = reg_res.json()["default_organization_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create Client
        client_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients",
            json={"client_code": "INGEST-01", "name": "Ingestion Client"},
            headers=headers
        )
        client_id = client_res.json()["id"]

        # Upload Dataset CSV
        csv_buffer = io.BytesIO()
        sample_valid_df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue()

        files = {"file": ("transactions.csv", csv_bytes, "text/csv")}
        upload_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/datasets/upload",
            files=files,
            headers=headers
        )
        assert upload_res.status_code == 201
        ds_data = upload_res.json()
        assert ds_data["row_count"] == 100
        assert ds_data["target_column"] == "is_fraud"
        assert ds_data["validation_status"] in ["VALID", "WARNINGS"]
