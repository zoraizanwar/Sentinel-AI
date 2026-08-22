"""Sentinel AI — End-to-End Acceptance Test Suite.

Verifies the complete multi-tenant, multi-client, persistent ML, RBAC,
audit trail, and PDF reporting lifecycle on localhost.
"""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEndToEndAcceptance:
    """Comprehensive E2E acceptance tests for Phase 9 & portfolio readiness."""

    async def test_complete_enterprise_lifecycle(self, async_client: AsyncClient):
        ac = async_client

        # 1. Register Organization Admin for Org A
        reg_a = await ac.post("/api/v1/auth/register", json={
            "email": "admin@alpha-corp.com",
            "password": "Password123!",
            "full_name": "Alpha Admin",
            "organization_name": "Alpha Corp Risk"
        })
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        org_a_id = reg_a.json()["default_organization_id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Register Organization Admin for Org B (Tenant Isolation Test)
        reg_b = await ac.post("/api/v1/auth/register", json={
            "email": "admin@beta-bank.com",
            "password": "Password123!",
            "full_name": "Beta Admin",
            "organization_name": "Beta Bank Global"
        })
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. Org A creates two clients: Client 1 and Client 2
        c1_resp = await ac.post(f"/api/v1/organizations/{org_a_id}/clients", json={
            "client_code": "BOA",
            "name": "Bank of America Retail",
            "industry": "Banking"
        }, headers=headers_a)
        assert c1_resp.status_code == 201
        c1_id = c1_resp.json()["id"]

        c2_resp = await ac.post(f"/api/v1/organizations/{org_a_id}/clients", json={
            "client_code": "CITI",
            "name": "Citigroup Operations",
            "industry": "Investment Banking"
        }, headers=headers_a)
        assert c2_resp.status_code == 201
        c2_id = c2_resp.json()["id"]

        # 4. Verify Org B CANNOT view or access Org A's clients (Strict Tenant Isolation)
        b_probe = await ac.get(f"/api/v1/organizations/{org_a_id}/clients", headers=headers_b)
        assert b_probe.status_code in [403, 404]

        # 5. Upload Dataset to Org A -> Client 1
        csv_content = (
            "trans_date_trans_time,cc_num,merchant,category,amt,first,last,gender,street,city,state,zip,lat,long,city_pop,job,dob,trans_num,unix_time,merch_lat,merch_long,is_fraud\n"
            "2020-01-01 12:00:00,1234567890123456,fraud_Kirlin and Sons,shopping_net,250.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_001,1577880000,32.78,-96.80,1\n"
            "2020-01-01 13:00:00,1234567890123456,fraud_Kirlin and Sons,grocery_pos,15.50,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_002,1577883600,32.77,-96.79,0\n"
            "2020-01-01 14:00:00,1234567890123456,fraud_Kirlin and Sons,gas_transport,45.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_003,1577887200,32.77,-96.79,0\n"
            "2020-01-01 15:00:00,1234567890123456,fraud_Kirlin and Sons,shopping_net,950.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_004,1577890800,32.85,-96.85,1\n"
            "2020-01-01 16:00:00,1234567890123456,fraud_Kirlin and Sons,entertainment,35.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_005,1577894400,32.77,-96.79,0\n"
            "2020-01-01 17:00:00,1234567890123456,fraud_Kirlin and Sons,grocery_pos,22.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_006,1577898000,32.77,-96.79,0\n"
            "2020-01-01 18:00:00,1234567890123456,fraud_Kirlin and Sons,shopping_net,500.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_007,1577901600,32.80,-96.82,1\n"
            "2020-01-01 19:00:00,1234567890123456,fraud_Kirlin and Sons,misc_net,12.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_008,1577905200,32.77,-96.79,0\n"
            "2020-01-01 20:00:00,1234567890123456,fraud_Kirlin and Sons,shopping_pos,40.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_009,1577908800,32.77,-96.79,0\n"
            "2020-01-01 21:00:00,1234567890123456,fraud_Kirlin and Sons,grocery_pos,18.00,John,Doe,M,123 Main,Dallas,TX,75001,32.77,-96.79,1300000,Engineer,1980-01-01,tx_010,1577912400,32.77,-96.79,0\n"
        )
        files = {"file": ("e2e_transactions.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        ds_resp = await ac.post(
            f"/api/v1/organizations/{org_a_id}/clients/{c1_id}/datasets/upload",
            files=files,
            headers=headers_a
        )
        assert ds_resp.status_code == 201
        dataset_id = ds_resp.json()["id"]

        # 6. Execute ML Analysis Pipeline on Dataset
        analysis_resp = await ac.post(
            f"/api/v1/organizations/{org_a_id}/clients/{c1_id}/datasets/{dataset_id}/analyze",
            headers=headers_a
        )
        assert analysis_resp.status_code == 201
        analysis_id = analysis_resp.json()["id"]
        assert analysis_resp.json()["status"] == "COMPLETED"

        # 7. Query Indexed Transactions
        tx_resp = await ac.get(
            f"/api/v1/organizations/{org_a_id}/analyses/{analysis_id}/transactions",
            params={"page": 1, "page_size": 10, "sort_by": "risk_score", "sort_order": "desc"},
            headers=headers_a
        )
        assert tx_resp.status_code == 200
        txs = tx_resp.json()["transactions"]
        assert len(txs) > 0
        top_tx_id = txs[0]["transaction_id"]

        # 8. SHAP Local Explainability
        explain_resp = await ac.get(
            f"/api/v1/organizations/{org_a_id}/analyses/{analysis_id}/transactions/{top_tx_id}/explain",
            headers=headers_a
        )
        assert explain_resp.status_code == 200
        assert "positive_contributions" in explain_resp.json()

        # 9. Generate and Download Client-Scope PDF Report
        report_resp = await ac.post(
            f"/api/v1/organizations/{org_a_id}/reports/generate",
            json={
                "client_id": c1_id,
                "analysis_id": analysis_id,
                "report_type": "CLIENT",
                "title": "E2E Acceptance Client Report"
            },
            headers=headers_a
        )
        assert report_resp.status_code == 201
        report_id = report_resp.json()["id"]

        dl_resp = await ac.get(
            f"/api/v1/organizations/{org_a_id}/reports/{report_id}/download",
            headers=headers_a
        )
        assert dl_resp.status_code == 200
        assert dl_resp.headers["content-type"] == "application/pdf"
        assert dl_resp.content.startswith(b"%PDF")

        # 10. Audit Trail Verification
        audit_resp = await ac.get(
            f"/api/v1/organizations/{org_a_id}/audit-logs",
            headers=headers_a
        )
        assert audit_resp.status_code == 200
        audit_json = audit_resp.json()
        assert audit_json["total_count"] > 0
        actions = [l["action"] for l in audit_json["items"]]
        assert "CLIENT_CREATED" in actions
        assert "DATASET_UPLOADED" in actions
        assert "ANALYSIS_COMPLETED" in actions
        assert "REPORT_GENERATED" in actions
