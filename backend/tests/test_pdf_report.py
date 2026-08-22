"""Automated Testing Suite for ReportLab PDF Report Generation Engine."""
import io
import pytest
import pypdf
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.session_store import session_store
from backend.app.services.reporting.pdf_report import PDFReportGenerator
from backend.app.services.analysis_service import analysis_service




@pytest.fixture
def active_session(sample_valid_df):
    """Creates a full valid in-memory session for testing."""
    session_store.clear()
    analysis_result, session = analysis_service.run_analysis(
        df=sample_valid_df,
        filename="test_transactions.csv",
        file_size_bytes=10240
    )
    return session


class TestPDFReportGeneration:

    def test_direct_pdf_generator_output(self, active_session):
        pdf_bytes = PDFReportGenerator.generate_report(active_session)

        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 5000  # Multi-page PDF with embedded charts
        assert pdf_bytes.startswith(b'%PDF-')

        # Read PDF content with pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 4

        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() or ""

        # Verify key sections exist in generated PDF
        assert "SENTINEL AI" in full_text
        assert "Fraud Intelligence & Risk Analysis Report" in full_text
        assert "01. Executive Summary" in full_text
        assert "02. Dataset Integrity" in full_text
        assert "03. Calibrated Risk Tier Segmentation" in full_text
        assert "05. Machine Learning Model Benchmarking" in full_text
        assert "07. Sample High-Risk Transactions Queue" in full_text
        assert "08. Empirical Analytical Findings" in full_text
        assert "10. Machine Learning & Engineering Methodology" in full_text
        assert "11. Operational Limitations" in full_text

        # Verify zero PII leakage
        assert "cc_num" not in full_text
        assert "400000000000" not in full_text

    def test_pdf_endpoint_success(self, client, active_session):
        analysis_id = active_session.analysis_id
        response = client.post(f"/api/v1/analysis/{analysis_id}/report/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert f"sentinel_ai_fraud_intelligence_report_{analysis_id}.pdf" in response.headers["content-disposition"]
        assert len(response.content) > 5000
        assert response.content.startswith(b'%PDF-')

    def test_pdf_endpoint_missing_analysis_404(self, client):
        response = client.post("/api/v1/analysis/00000000-0000-0000-0000-000000000000/report/pdf")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "ANALYSIS_NOT_FOUND"

    def test_pdf_generation_preserves_session_immutability(self, client, active_session):
        analysis_id = active_session.analysis_id
        original_tx_count = len(active_session.predictions_df)
        original_model = active_session.model_name

        # Trigger PDF generation
        response = client.post(f"/api/v1/analysis/{analysis_id}/report/pdf")
        assert response.status_code == 200

        # Verify session state is completely unmutated
        retrieved = session_store.get(analysis_id)
        assert len(retrieved.predictions_df) == original_tx_count
        assert retrieved.model_name == original_model
        assert retrieved.analysis_result.fraud_statistics.total_transactions == active_session.analysis_result.fraud_statistics.total_transactions
