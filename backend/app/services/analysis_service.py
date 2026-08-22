"""End-to-End Fraud Analysis Orchestration Service for Sentinel AI.
Coordinates ingestion, validation, feature engineering, model training,
threshold optimization, risk scoring, analytics, and session creation.
"""
import time
from typing import Optional, Tuple, Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ..schemas.validation import DatasetInspectionResult, DataQualityReport, ValidationStatus
from ..schemas.analysis import AnalysisResult, TransactionPaginationMeta
from ..core.session_store import session_store, AnalysisSession
from ..core.exceptions import DatasetValidationError, AnalysisExecutionError
from .ingestion.validator import DatasetValidator
from .ml.feature_engineering import FeatureEngineeringPipeline
from .ml.preprocessor import LeakFreePreprocessor
from .ml.models import ModelTrainer
from .ml.risk_scorer import RiskScorer
from .ml.evaluator import ModelEvaluator
from .ml.explainers import TransactionExplainer
from .analytics.aggregations import AnalyticsEngine
from .analytics.recommendations import RecommendationEngine


class AnalysisService:
    """Orchestrates the entire machine learning and analytics workflow."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state

    def inspect_dataset(self, df: pd.DataFrame, filename: str, file_size_bytes: int) -> DatasetInspectionResult:
        """Runs fast pre-flight validation on an uploaded DataFrame without training models."""
        validator = DatasetValidator(df=df, dataset_name=filename, file_size_bytes=file_size_bytes)
        return validator.validate()

    def run_analysis(
        self,
        df: pd.DataFrame,
        filename: str,
        file_size_bytes: int,
        test_df: Optional[pd.DataFrame] = None
    ) -> Tuple[AnalysisResult, AnalysisSession]:
        """
        Executes complete fraud intelligence pipeline:
        Validation -> Feature Engineering -> Stratified Split -> Leak-Free Preprocessing ->
        Candidate Training -> Threshold Optimization -> Risk Scoring -> Analytics -> Session Storage.
        """
        start_time = time.time()

        # 1. Validate Dataset Integrity
        inspection_result = self.inspect_dataset(df, filename, file_size_bytes)
        if inspection_result.validation_status == ValidationStatus.INVALID:
            error_msgs = "; ".join([e.message for e in inspection_result.errors])
            raise DatasetValidationError(f"Dataset validation failed: {error_msgs}", code="DATASET_INVALID")

        target_col = inspection_result.target_column
        if not target_col or target_col not in df.columns:
            raise DatasetValidationError("Valid target column is missing from dataset.", code="MISSING_TARGET")

        # 2. Extract Features & Separate Metadata
        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target_series = fe.extract_features(df)

        if target_series is None or len(np.unique(target_series)) < 2:
            raise DatasetValidationError("Dataset must contain both legitimate and fraud examples.", code="SINGLE_CLASS")

        # 3. Stratified Train / Validation Split (75% Train / 25% Validation)
        X_train_df, X_val_df, y_train, y_val = train_test_split(
            features_df,
            target_series,
            test_size=0.25,
            random_state=self.random_state,
            stratify=target_series
        )

        # 4. Leak-Free Preprocessing (Fit on Train Only)
        preprocessor = LeakFreePreprocessor()
        X_train_proc = preprocessor.fit_transform(X_train_df)
        X_val_proc = preprocessor.transform(X_val_df)
        # Also transform full dataset for transaction explorer predictions
        X_full_proc = preprocessor.transform(features_df)
        feature_names = preprocessor.get_feature_names()

        # 5. Candidate Model Training, Evaluation & Model Selection
        trainer = ModelTrainer(random_state=self.random_state)
        val_summary, best_model, best_name, opt_thresh = trainer.train_and_evaluate_candidates(
            X_train=X_train_proc,
            y_train=y_train.values,
            X_val=X_val_proc,
            y_val=y_val.values,
            feature_names=feature_names
        )

        # 6. Generate Probabilities & Risk Scores across Full Dataset
        if hasattr(best_model, "predict_proba"):
            full_probs = best_model.predict_proba(X_full_proc)[:, 1]
        elif hasattr(best_model, "decision_function"):
            dec = best_model.decision_function(X_full_proc)
            full_probs = 1.0 / (1.0 + np.exp(-dec))
        else:
            full_probs = best_model.predict(X_full_proc).astype(float)

        risk_scores, risk_bands = RiskScorer.batch_score(full_probs)
        predicted_fraud = (full_probs >= opt_thresh).astype(int)

        # 7. Build In-Memory Predictions DataFrame for Transaction Explorer
        predictions_df = metadata_df.copy()
        if "amt" in df.columns:
            predictions_df["amt"] = df["amt"]
        if "category" in df.columns:
            predictions_df["category"] = df["category"]
        if "merchant" in df.columns:
            predictions_df["merchant"] = df["merchant"]
        if "city" in df.columns:
            predictions_df["city"] = df["city"]
        if "state" in df.columns:
            predictions_df["state"] = df["state"]
        if "trans_date_trans_time" in df.columns:
            predictions_df["trans_date_trans_time"] = df["trans_date_trans_time"]

        predictions_df["fraud_probability"] = np.round(full_probs, 4)
        predictions_df["risk_score"] = risk_scores
        predictions_df["risk_band"] = risk_bands
        predictions_df["predicted_fraud"] = predicted_fraud
        predictions_df["is_actual_fraud"] = target_series.values

        # 8. Unseen Test Evaluation (if test_df provided)
        test_metrics = None
        if test_df is not None:
            try:
                test_feat_df, _, test_target = fe.extract_features(test_df)
                if test_target is not None:
                    X_test_proc = preprocessor.transform(test_feat_df)
                    if hasattr(best_model, "predict_proba"):
                        test_probs = best_model.predict_proba(X_test_proc)[:, 1]
                    else:
                        test_probs = best_model.predict(X_test_proc).astype(float)

                    test_metrics = ModelEvaluator.evaluate(
                        model_name=best_name,
                        y_true=test_target.values,
                        y_prob=test_probs,
                        threshold=opt_thresh
                    )
                    val_summary.test_metrics = test_metrics
                    val_summary.test_fraud_count = int(np.sum(test_target.values == 1))
                    val_summary.test_legit_count = int(np.sum(test_target.values == 0))
            except Exception:
                pass

        # 9. Statistical Aggregations & Analytics
        fraud_stats = AnalyticsEngine.compute_fraud_statistics(df, target_col=target_col, amount_col="amt")
        risk_stats = AnalyticsEngine.compute_risk_statistics(risk_scores, risk_bands)
        risk_dist = AnalyticsEngine.compute_risk_distribution(risk_scores, y_true=target_series.values)
        cat_breakdowns = AnalyticsEngine.compute_categorical_breakdowns(df, target_col=target_col)
        patterns = AnalyticsEngine.detect_risk_patterns(df, target_col=target_col)

        # 10. Analytical Findings & Recommendations
        selected_cand_metrics = next(m for m in val_summary.candidate_models if m.model_name == best_name)
        findings, recommendations = RecommendationEngine.generate_findings_and_recommendations(
            fraud_stats=fraud_stats,
            category_breakdowns=cat_breakdowns,
            patterns=patterns,
            selected_model=val_summary.selected_model,
            model_metrics=selected_cand_metrics
        )

        # 11. Compile Data Quality Report
        quality_report = DataQualityReport(
            is_valid_for_analysis=True,
            total_rows=len(df),
            total_columns=len(df.columns),
            missing_cells_percentage=round((inspection_result.total_missing_cells / (len(df)*len(df.columns))) * 100.0, 2) if len(df) > 0 else 0.0,
            duplicate_rows_percentage=round((inspection_result.duplicate_rows_count / len(df)) * 100.0, 2) if len(df) > 0 else 0.0,
            has_target=True,
            target_column_name=target_col,
            fraud_rate_percentage=fraud_stats.fraud_rate_percentage,
            validation_findings_count={
                "errors": len(inspection_result.errors),
                "warnings": len(inspection_result.warnings),
                "infos": len(inspection_result.infos)
            },
            findings=inspection_result.errors + inspection_result.warnings + inspection_result.infos
        )

        elapsed = round(time.time() - start_time, 2)

        # 12. Create Master AnalysisResult Schema
        analysis_result = AnalysisResult(
            analysis_id="",  # Populated during session creation
            execution_time_seconds=elapsed,
            dataset_summary=inspection_result,
            data_quality=quality_report,
            fraud_statistics=fraud_stats,
            risk_statistics=risk_stats,
            model_results=val_summary,
            risk_distribution=risk_dist,
            categorical_breakdowns=cat_breakdowns,
            high_risk_patterns=patterns,
            findings=findings,
            recommendations=recommendations,
            pagination_meta=TransactionPaginationMeta(
                total_records=len(predictions_df),
                page=1,
                page_size=50,
                total_pages=int(np.ceil(len(predictions_df) / 50.0))
            )
        )

        # 13. Initialize SHAP Explainer
        explainer = TransactionExplainer(
            model=best_model,
            feature_names=feature_names,
            background_sample=X_train_proc[:50]
        )

        # 14. Register Session in Thread-Safe Store
        session = session_store.create(
            raw_filename=filename,
            dataset=df,
            validation_report=quality_report,
            preprocessor_pipeline=preprocessor,
            trained_model=best_model,
            model_name=best_name,
            optimal_threshold=opt_thresh,
            feature_names=feature_names,
            predictions_df=predictions_df,
            analysis_result=analysis_result,
            shap_explainer=explainer
        )

        return analysis_result, session


# Global Singleton Analysis Service
analysis_service = AnalysisService()
