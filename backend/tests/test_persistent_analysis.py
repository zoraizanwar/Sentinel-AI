"""Automated Tests for Persistent Analysis, Transaction Explorer and SHAP."""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPersistentAnalysis:

    async def test_end_to_end_analysis_persistence_and_transactions(
        self,
        async_client: AsyncClient,
        sample_valid_df
    ):
        # 1. Register User & Org
        reg_res = await async_client.post("/api/v1/auth/register", json={
            "email": "analyst@mlrisk.com",
            "password": "SecretPassword123",
            "full_name": "Senior ML Analyst",
            "organization_name": "ML Risk Intelligence"
        })
        token = reg_res.json()["access_token"]
        org_id = reg_res.json()["default_organization_id"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Client
        client_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients",
            json={"client_code": "CL-ML-01", "name": "Global Retail Bank"},
            headers=headers
        )
        client_id = client_res.json()["id"]

        # 3. Upload Dataset
        csv_buffer = io.BytesIO()
        sample_valid_df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue()

        files = {"file": ("credit_transactions.csv", csv_bytes, "text/csv")}
        upload_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/datasets/upload",
            files=files,
            headers=headers
        )
        dataset_id = upload_res.json()["id"]

        # 4. Trigger Persistent Analysis
        analyze_res = await async_client.post(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/datasets/{dataset_id}/analyze",
            headers=headers
        )
        assert analyze_res.status_code == 201
        analysis_data = analyze_res.json()
        analysis_id = analysis_data["id"]
        assert analysis_data["model_name"] in ["Random Forest", "Logistic Regression", "XGBoost (Candidate)", "RandomForestClassifier", "LogisticRegression"]
        assert analysis_data["fraud_statistics"]["total_transactions"] == 100
        assert analysis_data["status"] == "COMPLETED"

        # 5. Query Transactions Explorer with Pagination & Filters
        tx_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/analyses/{analysis_id}/transactions?page=1&page_size=25&sort_by=risk_score&sort_order=desc",
            headers=headers
        )
        assert tx_res.status_code == 200
        tx_page = tx_res.json()
        assert tx_page["total_matching"] == 100
        assert len(tx_page["transactions"]) == 25
        first_tx = tx_page["transactions"][0]
        first_tx_num = first_tx["transaction_id"]

        # 6. Query SHAP Explanation for First Transaction
        explain_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/analyses/{analysis_id}/transactions/{first_tx_num}/explain",
            headers=headers
        )
        assert explain_res.status_code == 200
        explain_data = explain_res.json()
        assert explain_data["transaction_id"] == first_tx_num
        assert "risk_score" in explain_data
        assert "positive_contributions" in explain_data

        # 7. Check Client Dashboard
        dash_res = await async_client.get(
            f"/api/v1/organizations/{org_id}/clients/{client_id}/dashboard",
            headers=headers
        )
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert dash_data["total_transactions"] == 100
        assert dash_data["client"]["id"] == client_id
