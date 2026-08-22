"""Automated Integration Tests for FastAPI REST Endpoints."""
import io
import pytest
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.session_store import session_store




@pytest.fixture
def small_csv_bytes(sample_valid_df):
    """Generates small in-memory CSV bytes from sample_valid_df."""
    buffer = io.BytesIO()
    sample_valid_df.to_csv(buffer, index=False)
    buffer.seek(0)
    return buffer.getvalue()


class TestFastAPIEndpoints:

    # 1. Health Check
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "sentinel-ai"
        assert "version" in data

    # 2. Pre-flight Dataset Inspection
    def test_dataset_inspect_endpoint(self, client, small_csv_bytes):
        files = {"file": ("test_upload.csv", small_csv_bytes, "text/csv")}
        response = client.post("/api/v1/dataset/inspect", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["row_count"] == 100
        assert data["target_column"] == "is_fraud"
        assert data["validation_status"] in ["VALID", "WARNINGS"]
        assert len(data["errors"]) == 0

    # 3. Invalid File Extension on Inspect
    def test_inspect_invalid_extension(self, client):
        files = {"file": ("data.xlsx", b"dummy content", "application/vnd.ms-excel")}
        response = client.post("/api/v1/dataset/inspect", files=files)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_FILE_EXTENSION"

    # 4. Empty File on Inspect
    def test_inspect_empty_file(self, client):
        files = {"file": ("empty.csv", b"", "text/csv")}
        response = client.post("/api/v1/dataset/inspect", files=files)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "EMPTY_FILE"

    # 5. Full Analysis Run & Retrieval Flow
    def test_analysis_run_and_retrieve_flow(self, client, small_csv_bytes):
        # Trigger Analysis Run
        files = {"file": ("transactions.csv", small_csv_bytes, "text/csv")}
        run_resp = client.post("/api/v1/analysis/run", files=files)

        assert run_resp.status_code == 200
        result_data = run_resp.json()
        analysis_id = result_data["analysis_id"]
        assert analysis_id != ""
        assert result_data["fraud_statistics"]["total_transactions"] == 100
        assert "selected_model" in result_data["model_results"]
        assert len(result_data["findings"]) > 0
        assert len(result_data["recommendations"]) > 0

        # Retrieve Analysis Result
        get_resp = client.get(f"/api/v1/analysis/{analysis_id}")
        assert get_resp.status_code == 200
        retrieved_data = get_resp.json()
        assert retrieved_data["analysis_id"] == analysis_id
        assert retrieved_data["fraud_statistics"]["total_transactions"] == 100

    # 6. Missing Analysis ID 404
    def test_get_non_existent_analysis(self, client):
        response = client.get("/api/v1/analysis/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "ANALYSIS_NOT_FOUND"

    # 7. Transaction Explorer Pagination & Filtering
    def test_transactions_explorer_and_filters(self, client, small_csv_bytes):
        # Run analysis first
        files = {"file": ("tx_data.csv", small_csv_bytes, "text/csv")}
        run_resp = client.post("/api/v1/analysis/run", files=files)
        analysis_id = run_resp.json()["analysis_id"]

        # Default query
        tx_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions?page=1&page_size=10")
        assert tx_resp.status_code == 200
        tx_data = tx_resp.json()
        assert tx_data["total_matching"] == 100
        assert len(tx_data["transactions"]) == 10
        assert tx_data["page"] == 1
        assert tx_data["total_pages"] == 10

        # Filter by risk band
        low_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions?risk_band=LOW")
        assert low_resp.status_code == 200
        low_data = low_resp.json()
        assert all(t["risk_band"] == "LOW" for t in low_data["transactions"])

        # Filter by amount range
        amt_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions?min_amount=100.0&max_amount=300.0")
        assert amt_resp.status_code == 200
        amt_data = amt_resp.json()
        assert all(100.0 <= t["amount"] <= 300.0 for t in amt_data["transactions"])

        # Search query
        search_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions?search=tx_0005")
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert search_data["total_matching"] >= 1
        assert any(t["transaction_id"] == "tx_0005" for t in search_data["transactions"])

    # 8. On-Demand SHAP Explanation Endpoint
    def test_explain_transaction_endpoint(self, client, small_csv_bytes):
        files = {"file": ("tx_explain.csv", small_csv_bytes, "text/csv")}
        run_resp = client.post("/api/v1/analysis/run", files=files)
        analysis_id = run_resp.json()["analysis_id"]

        # Explain transaction tx_0001
        exp_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions/tx_0001/explain")
        assert exp_resp.status_code == 200
        exp_data = exp_resp.json()
        assert exp_data["transaction_id"] == "tx_0001"
        assert 0.0 <= exp_data["fraud_probability"] <= 1.0
        assert 0.0 <= exp_data["risk_score"] <= 100.0
        assert exp_data["risk_band"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert exp_data["is_cached"] is False

        # Repeated call returns cached
        exp_cached_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions/tx_0001/explain")
        assert exp_cached_resp.status_code == 200
        assert exp_cached_resp.json()["is_cached"] is True

    # 9. Explain Non-Existent Transaction 404
    def test_explain_non_existent_transaction(self, client, small_csv_bytes):
        files = {"file": ("tx_explain.csv", small_csv_bytes, "text/csv")}
        run_resp = client.post("/api/v1/analysis/run", files=files)
        analysis_id = run_resp.json()["analysis_id"]

        exp_resp = client.get(f"/api/v1/analysis/{analysis_id}/transactions/tx_NON_EXISTENT/explain")
        assert exp_resp.status_code == 404
        assert exp_resp.json()["error_code"] == "TRANSACTION_NOT_FOUND"

    # 10. PDF Report Endpoint Returns 200 and application/pdf
    def test_pdf_report_endpoint(self, client, small_csv_bytes):
        files = {"file": ("tx_report.csv", small_csv_bytes, "text/csv")}
        run_resp = client.post("/api/v1/analysis/run", files=files)
        analysis_id = run_resp.json()["analysis_id"]

        rep_resp = client.post(f"/api/v1/analysis/{analysis_id}/report/pdf")
        assert rep_resp.status_code == 200
        assert rep_resp.headers["content-type"] == "application/pdf"
        assert f"sentinel_ai_fraud_intelligence_report_{analysis_id}.pdf" in rep_resp.headers["content-disposition"]
        assert len(rep_resp.content) > 1000

