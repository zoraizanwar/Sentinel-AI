"""Automated Tests for Report Generation, Downloads, and Audit Logging."""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestReportsAndAudit:

    async def test_report_generation_download_and_audit_trail(
        self,
        async_client: AsyncClient,
        sample_valid_df
    ):
        # 1. Register User & Org
        reg_res = await async_client.post("/api/v1/auth/register", json={
            "email": "auditor@auditfirm.com",
            "password": "Password123",
            "full_name": "Chief Risk Auditor",
            "organization_name": "Audit & Compliance Corp"
        })
        token = reg_res.json()["access_token"]
        org_id = reg_res.json()["default_organization_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Client, Upload Dataset & Run Analysis
        client_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients",
            json={"client_code": "AUDIT-01", "name": "Audit Client"},
            headers=headers
        )
        client_id = client_res.json()["id"]

        csv_buffer = io.BytesIO()
        sample_valid_df.to_csv(csv_buffer, index=False)
        files = {"file": ("audit_tx.csv", csv_buffer.getvalue(), "text/csv")}
        upload_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/datasets/upload",
            files=files,
            headers=headers
        )
        dataset_id = upload_res.json()["id"]

        analyze_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/datasets/{dataset_id}/analyze",
            headers=headers
        )
        analysis_id = analyze_res.json()["id"]

        # 3. Generate Multi-Scope PDF Audit Report
        report_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/reports/generate",
            json={
                "report_type": "CLIENT",
                "client_id": client_id,
                "analysis_id": analysis_id,
                "title": "Executive Client Fraud Audit Report"
            },
            headers=headers
        )
        assert report_res.status_code == 201
        report_data = report_res.json()
        report_id = report_data["id"]
        assert report_data["title"] == "Executive Client Fraud Audit Report"
        assert report_data["file_size_bytes"] > 0

        # 4. Download PDF Report
        download_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/reports/{report_id}/download",
            headers=headers
        )
        assert download_res.status_code == 200
        assert download_res.headers["content-type"] == "application/pdf"
        assert len(download_res.content) > 0

        # 5. Query Audit Logs (ADMIN required)
        audit_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/audit-logs",
            headers=headers
        )
        assert audit_res.status_code == 200
        audit_data = audit_res.json()
        assert audit_data["total_count"] > 0
        actions = [log["action"] for log in audit_data["items"]]
        assert "REGISTRATION" in actions or "CLIENT_CREATED" in actions
