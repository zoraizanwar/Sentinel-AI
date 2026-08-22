"""Automated tests for In-Memory SessionStore and TTL lifecycle."""
import time
import pytest
import pandas as pd
from datetime import datetime, timedelta, timezone

from backend.app.core.session_store import SessionStore, AnalysisSession
from backend.app.core.exceptions import AnalysisNotFoundError
from backend.app.schemas.analysis import AnalysisResult, TransactionPaginationMeta, FraudStatistics, RiskStatistics, RiskDistributionSummary
from backend.app.schemas.validation import DataQualityReport, DatasetInspectionResult, ValidationStatus
from backend.app.schemas.ml import ModelEvaluationSummary, SelectedModelDetails


@pytest.fixture
def dummy_analysis_result():
    inspection = DatasetInspectionResult(
        dataset_name="test.csv",
        file_size_bytes=1000,
        row_count=100,
        column_count=5,
        target_column="is_fraud",
        validation_status=ValidationStatus.VALID
    )
    quality = DataQualityReport(
        is_valid_for_analysis=True,
        total_rows=100,
        total_columns=5,
        missing_cells_percentage=0.0,
        duplicate_rows_percentage=0.0,
        has_target=True,
        validation_findings_count={},
        findings=[]
    )
    return AnalysisResult(
        analysis_id="",
        execution_time_seconds=1.0,
        dataset_summary=inspection,
        data_quality=quality,
        fraud_statistics=FraudStatistics(
            total_transactions=100,
            fraud_count=5,
            legitimate_count=95,
            fraud_rate_percentage=5.0,
            total_volume_usd=10000.0,
            fraud_volume_usd=1500.0,
            fraud_loss_percentage=15.0
        ),
        risk_statistics=RiskStatistics(
            low_risk_count=90, low_risk_pct=90.0,
            medium_risk_count=5, medium_risk_pct=5.0,
            high_risk_count=3, high_risk_pct=3.0,
            critical_risk_count=2, critical_risk_pct=2.0,
            mean_risk_score=10.5, median_risk_score=5.0
        ),
        model_results=ModelEvaluationSummary(
            candidate_models=[],
            selected_model=SelectedModelDetails(
                model_name="Random Forest",
                justification="Test",
                selection_metric="PR-AUC",
                selection_value=0.9,
                optimal_threshold=0.5,
                threshold_methodology="Test"
            ),
            global_feature_importance=[],
            validation_fraud_count=5,
            validation_legit_count=95
        ),
        risk_distribution=RiskDistributionSummary(
            score_bins=["0-10", "10-20"],
            counts=[90, 10],
            fraud_counts_per_bin=[0, 5]
        ),
        pagination_meta=TransactionPaginationMeta(total_records=100, page=1, page_size=50, total_pages=2)
    )


class TestSessionStore:

    def test_session_create_and_retrieve(self, dummy_analysis_result):
        store = SessionStore(default_ttl_seconds=300)
        df = pd.DataFrame({"col": [1, 2, 3]})
        preds_df = pd.DataFrame({"trans_num": ["tx1", "tx2"], "risk_score": [10.0, 90.0]})

        session = store.create(
            raw_filename="test.csv",
            dataset=df,
            validation_report=dummy_analysis_result.data_quality,
            preprocessor_pipeline=None,
            trained_model=None,
            model_name="Random Forest",
            optimal_threshold=0.5,
            feature_names=["col"],
            predictions_df=preds_df,
            analysis_result=dummy_analysis_result
        )

        assert session.analysis_id != ""
        assert store.contains(session.analysis_id) is True
        assert store.count() == 1

        retrieved = store.get(session.analysis_id)
        assert retrieved.analysis_id == session.analysis_id
        assert retrieved.model_name == "Random Forest"
        assert len(retrieved.dataset) == 3

    def test_missing_session_raises_error(self):
        store = SessionStore()
        with pytest.raises(AnalysisNotFoundError):
            store.get("non-existent-uuid")

    def test_session_deletion(self, dummy_analysis_result):
        store = SessionStore()
        session = store.create(
            raw_filename="test.csv",
            dataset=pd.DataFrame(),
            validation_report=dummy_analysis_result.data_quality,
            preprocessor_pipeline=None,
            trained_model=None,
            model_name="Random Forest",
            optimal_threshold=0.5,
            feature_names=[],
            predictions_df=pd.DataFrame(),
            analysis_result=dummy_analysis_result
        )
        assert store.delete(session.analysis_id) is True
        assert store.contains(session.analysis_id) is False
        assert store.delete("non-existent") is False

    def test_ttl_expiry_and_cleanup(self, dummy_analysis_result):
        # 1-second TTL
        store = SessionStore(default_ttl_seconds=1)
        session = store.create(
            raw_filename="test.csv",
            dataset=pd.DataFrame(),
            validation_report=dummy_analysis_result.data_quality,
            preprocessor_pipeline=None,
            trained_model=None,
            model_name="Random Forest",
            optimal_threshold=0.5,
            feature_names=[],
            predictions_df=pd.DataFrame(),
            analysis_result=dummy_analysis_result,
            ttl_seconds=1
        )
        assert store.contains(session.analysis_id) is True
        time.sleep(1.1)

        # Accessing expired session raises error
        with pytest.raises(AnalysisNotFoundError):
            store.get(session.analysis_id)

        # Cleanup expired removes it
        pruned = store.cleanup_expired()
        assert store.count() == 0
