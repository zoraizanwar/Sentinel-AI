"""Persistent Machine Learning Analysis Service."""
import time
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sklearn.model_selection import train_test_split

from backend.app.config import settings
from backend.app.core.exceptions import SentinelAIException, DatasetValidationError
from backend.app.core.session_store import session_store, AnalysisSession
from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.dataset import Dataset, DatasetProcessingStatus
from backend.app.models.client import Client
from backend.app.repositories.analysis_repo import AnalysisRepository
from backend.app.repositories.dataset_repo import DatasetRepository
from backend.app.repositories.client_repo import ClientRepository
from backend.app.repositories.transaction_repo import TransactionRepository
from backend.app.services.audit_service import AuditService
from backend.app.services.ingestion.csv_source import CSVDataSource
from backend.app.services.ingestion.validator import DatasetValidator
from backend.app.services.ml.feature_engineering import FeatureEngineeringPipeline
from backend.app.services.ml.preprocessor import LeakFreePreprocessor
from backend.app.services.ml.models import ModelTrainer
from backend.app.services.ml.risk_scorer import RiskScorer
from backend.app.services.ml.explainers import TransactionExplainer
from backend.app.services.analytics.aggregations import AnalyticsEngine
from backend.app.services.analytics.recommendations import RecommendationEngine
from backend.app.schemas.persistent_analysis import PersistentAnalysisResponse, AnalysisListItemResponse
from backend.app.schemas.analysis import AnalysisResult, TransactionPaginationMeta
from backend.app.schemas.validation import DataQualityReport


class PersistentAnalysisService:
    def __init__(self, db: AsyncSession, random_state: int = 42):
        self.db = db
        self.random_state = random_state
        self.analysis_repo = AnalysisRepository(db)
        self.dataset_repo = DatasetRepository(db)
        self.client_repo = ClientRepository(db)
        self.tx_repo = TransactionRepository(db)
        self.audit_service = AuditService(db)

    async def list_analyses(self, org_id: str, client_id: Optional[str] = None) -> List[AnalysisListItemResponse]:
        if client_id:
            analyses = await self.analysis_repo.list_by_client(org_id, client_id)
        else:
            analyses = await self.analysis_repo.list_by_organization(org_id)

        results = []
        for a in analyses:
            client = await self.db.get(Client, a.client_id)
            dataset = await self.db.get(Dataset, a.dataset_id)
            f_stats = a.fraud_statistics or {}
            results.append(
                AnalysisListItemResponse(
                    id=a.id,
                    organization_id=a.organization_id,
                    client_id=a.client_id,
                    client_name=client.name if client else "Unknown",
                    client_code=client.client_code if client else "N/A",
                    dataset_id=a.dataset_id,
                    dataset_filename=dataset.filename if dataset else "dataset.csv",
                    model_name=a.model_name,
                    optimal_threshold=a.optimal_threshold,
                    execution_time_seconds=a.execution_time_seconds,
                    total_transactions=f_stats.get("total_transactions", 0),
                    fraud_transactions=f_stats.get("fraud_count", 0),
                    fraud_rate_percentage=f_stats.get("fraud_rate_percentage", 0.0),
                    financial_exposure_usd=f_stats.get("fraud_volume_usd", 0.0),
                    status=a.status,
                    created_at=a.created_at
                )
            )
        return results

    async def get_analysis(self, org_id: str, analysis_id: str) -> PersistentAnalysisResponse:
        analysis = await self.analysis_repo.get_by_id(org_id, analysis_id)
        if not analysis:
            raise SentinelAIException("Analysis not found.", status_code=404, code="ANALYSIS_NOT_FOUND")

        client = await self.db.get(Client, analysis.client_id)
        dataset = await self.db.get(Dataset, analysis.dataset_id)

        return PersistentAnalysisResponse(
            id=analysis.id,
            organization_id=analysis.organization_id,
            client_id=analysis.client_id,
            client_name=client.name if client else None,
            client_code=client.client_code if client else None,
            dataset_id=analysis.dataset_id,
            dataset_filename=dataset.filename if dataset else None,
            user_id=analysis.user_id,
            model_name=analysis.model_name,
            optimal_threshold=analysis.optimal_threshold,
            execution_time_seconds=analysis.execution_time_seconds,
            status=analysis.status,
            validation_metrics=analysis.validation_metrics,
            test_metrics=analysis.test_metrics,
            fraud_statistics=analysis.fraud_statistics,
            risk_statistics=analysis.risk_statistics,
            category_breakdown=analysis.category_breakdown,
            empirical_findings=analysis.empirical_findings,
            recommendations=analysis.recommendations,
            global_feature_importance=analysis.global_feature_importance,
            created_at=analysis.created_at
        )

    async def run_analysis(
        self,
        org_id: str,
        client_id: str,
        dataset_id: str,
        user_id: Optional[str] = None
    ) -> PersistentAnalysisResponse:
        client = await self.client_repo.get_by_id(org_id, client_id)
        if not client:
            raise SentinelAIException("Client not found in this organization.", status_code=404, code="CLIENT_NOT_FOUND")

        dataset = await self.dataset_repo.get_by_id(org_id, dataset_id)
        if not dataset or dataset.client_id != client_id:
            raise SentinelAIException("Dataset not found or does not belong to the selected client.", status_code=404, code="DATASET_NOT_FOUND")

        start_time = time.time()

        await self.audit_service.log_event(
            org_id=org_id,
            action="ANALYSIS_STARTED",
            resource_type="DATASET",
            resource_id=dataset.id,
            user_id=user_id,
            details={"client_code": client.client_code, "dataset_name": dataset.filename}
        )
        await self.db.commit()

        # 1. Ingest Dataset CSV and inspect from local storage
        csv_source = CSVDataSource(file_path=dataset.file_path)
        raw_df = csv_source.load_data()
        inspection_result = csv_source.inspect()
        target_col = inspection_result.target_column or "is_fraud"

        if target_col not in raw_df.columns:
            raise DatasetValidationError(f"Target column '{target_col}' not found in dataset.")

        # 3. Domain Feature Engineering
        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target_series = fe.extract_features(raw_df)

        if target_series is None or target_series.nunique() <= 1:
            raise DatasetValidationError("Dataset must contain both legitimate and fraud target examples for supervised model evaluation.", code="SINGLE_CLASS_TARGET")

        # 4. Stratified Train / Validation Split (75% / 25%)
        X_train_df, X_val_df, y_train, y_val = train_test_split(
            features_df,
            target_series,
            test_size=0.25,
            random_state=self.random_state,
            stratify=target_series
        )

        # 5. Leak-Free Preprocessing (Fit on Train Only)
        preprocessor = LeakFreePreprocessor()
        X_train_proc = preprocessor.fit_transform(X_train_df)
        X_val_proc = preprocessor.transform(X_val_df)
        X_full_proc = preprocessor.transform(features_df)
        feature_names = preprocessor.get_feature_names()

        # 6. Candidate Model Training & Model Selection
        trainer = ModelTrainer(random_state=self.random_state)
        val_summary, best_model, best_name, opt_thresh = trainer.train_and_evaluate_candidates(
            X_train=X_train_proc,
            y_train=y_train.values,
            X_val=X_val_proc,
            y_val=y_val.values,
            feature_names=feature_names
        )

        # 7. Generate Probabilities & Vectorized Risk Scores
        if hasattr(best_model, "predict_proba"):
            full_probs = best_model.predict_proba(X_full_proc)[:, 1]
        elif hasattr(best_model, "decision_function"):
            dec = best_model.decision_function(X_full_proc)
            full_probs = 1.0 / (1.0 + np.exp(-dec))
        else:
            full_probs = best_model.predict(X_full_proc).astype(float)

        risk_scores, risk_bands = RiskScorer.batch_score(full_probs)
        predicted_fraud = (full_probs >= opt_thresh).astype(int)

        # 8. Enrich Predictions DataFrame
        scored_df = raw_df.copy()
        scored_df["fraud_probability"] = np.round(full_probs, 4)
        scored_df["risk_score"] = risk_scores
        scored_df["risk_band"] = risk_bands
        scored_df["predicted_fraud"] = predicted_fraud
        scored_df["is_fraud_pred"] = predicted_fraud

        # 9. Statistical Aggregations & Analytics
        fraud_stats = AnalyticsEngine.compute_fraud_statistics(raw_df, target_col=target_col, amount_col="amt")
        risk_stats = AnalyticsEngine.compute_risk_statistics(risk_scores, risk_bands)
        risk_dist = AnalyticsEngine.compute_risk_distribution(risk_scores, y_true=target_series.values)
        cat_breakdowns = AnalyticsEngine.compute_categorical_breakdowns(raw_df, target_col=target_col)
        patterns = AnalyticsEngine.detect_risk_patterns(raw_df, target_col=target_col)

        # 10. Analytical Findings & Recommendations
        selected_cand_metrics = next(m for m in val_summary.candidate_models if m.model_name == best_name)
        findings, recommendations = RecommendationEngine.generate_findings_and_recommendations(
            fraud_stats=fraud_stats,
            category_breakdowns=cat_breakdowns,
            patterns=patterns,
            selected_model=val_summary.selected_model,
            model_metrics=selected_cand_metrics
        )

        exec_time = round(time.time() - start_time, 2)

        # 11. Compile Data Quality and Summary
        quality_report = DataQualityReport(
            is_valid_for_analysis=True,
            total_rows=len(raw_df),
            total_columns=len(raw_df.columns),
            missing_cells_percentage=round((inspection_result.total_missing_cells / (len(raw_df)*len(raw_df.columns))) * 100.0, 2) if len(raw_df) > 0 else 0.0,
            duplicate_rows_percentage=round((inspection_result.duplicate_rows_count / len(raw_df)) * 100.0, 2) if len(raw_df) > 0 else 0.0,
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

        # 12. Persist Analysis Record in PostgreSQL
        cat_list = [c.model_dump() for c in cat_breakdowns.values()] if isinstance(cat_breakdowns, dict) else [c.model_dump() for c in cat_breakdowns]

        analysis = await self.analysis_repo.create(
            org_id=org_id,
            client_id=client_id,
            dataset_id=dataset_id,
            user_id=user_id,
            model_name=best_name,
            optimal_threshold=opt_thresh,
            execution_time_seconds=exec_time,
            validation_metrics=val_summary.model_dump(),
            test_metrics=None,
            fraud_statistics=fraud_stats.model_dump(),
            risk_statistics=risk_stats.model_dump(),
            category_breakdown=cat_list,
            empirical_findings=[f.model_dump() for f in findings],
            recommendations=[r.model_dump() for r in recommendations],
            global_feature_importance=[f.model_dump() for f in val_summary.global_feature_importance],
            status=AnalysisStatus.COMPLETED
        )

        # 13. Batched Bulk Insert of Analyzed Transactions
        tx_records = []
        for idx, row in scored_df.iterrows():
            tx_records.append({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "client_id": client_id,
                "analysis_id": analysis.id,
                "transaction_num": str(row.get("trans_num", f"tx_{idx:06d}")),
                "timestamp": str(row.get("trans_date_trans_time", "")),
                "merchant": str(row.get("merchant", "")) if pd.notna(row.get("merchant")) else None,
                "category": str(row.get("category", "")) if pd.notna(row.get("category")) else None,
                "amount": float(row.get("amt", 0.0)),
                "city": str(row.get("city", "")) if pd.notna(row.get("city")) else None,
                "state": str(row.get("state", "")) if pd.notna(row.get("state")) else None,
                "lat": float(row["lat"]) if "lat" in row and pd.notna(row.get("lat")) else None,
                "long": float(row["long"]) if "long" in row and pd.notna(row.get("long")) else None,
                "merch_lat": float(row["merch_lat"]) if "merch_lat" in row and pd.notna(row.get("merch_lat")) else None,
                "merch_long": float(row["merch_long"]) if "merch_long" in row and pd.notna(row.get("merch_long")) else None,
                "is_fraud_pred": int(row.get("is_fraud_pred", 0)),
                "actual_fraud_label": int(row[target_col]) if target_col in row and pd.notna(row[target_col]) else None,
                "fraud_probability": float(row["fraud_probability"]),
                "risk_score": float(row["risk_score"]),
                "risk_band": str(row["risk_band"])
            })

        await self.tx_repo.bulk_insert(tx_records)
        await self.dataset_repo.update_status(dataset, DatasetProcessingStatus.ANALYZED)

        # 14. SessionStore Caching for Local Explainability
        explainer = TransactionExplainer(
            model=best_model,
            feature_names=feature_names,
            background_sample=X_train_proc[:50] if len(X_train_proc) > 0 else None
        )

        analysis_result_dto = AnalysisResult(
            analysis_id=analysis.id,
            created_at=analysis.created_at,
            execution_time_seconds=exec_time,
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
                total_records=len(raw_df),
                page=1,
                page_size=50,
                total_pages=max(1, int(np.ceil(len(raw_df)/50)))
            )
        )

        predictions_df = metadata_df.copy()
        for col in ["amt", "category", "merchant", "city", "state", "trans_date_trans_time"]:
            if col in raw_df.columns:
                predictions_df[col] = raw_df[col]
        predictions_df["fraud_probability"] = np.round(full_probs, 4)
        predictions_df["risk_score"] = risk_scores
        predictions_df["risk_band"] = risk_bands
        predictions_df["predicted_fraud"] = predicted_fraud
        predictions_df["is_actual_fraud"] = target_series.values

        now_utc = datetime.now(timezone.utc)
        session = AnalysisSession(
            analysis_id=analysis.id,
            created_at=now_utc,
            expires_at=now_utc + timedelta(seconds=settings.SESSION_TTL_SECONDS),
            raw_filename=dataset.filename,
            dataset=raw_df,
            validation_report=quality_report,
            preprocessor_pipeline=preprocessor,
            trained_model=best_model,
            model_name=best_name,
            optimal_threshold=opt_thresh,
            feature_names=feature_names,
            predictions_df=predictions_df,
            analysis_result=analysis_result_dto,
            shap_explainer=explainer
        )
        session_store.put(session)

        # 15. Audit Log
        await self.audit_service.log_event(
            org_id=org_id,
            action="ANALYSIS_COMPLETED",
            resource_type="ANALYSIS",
            resource_id=analysis.id,
            user_id=user_id,
            details={
                "model_name": best_name,
                "total_transactions": len(scored_df),
                "fraud_count": fraud_stats.fraud_count,
                "execution_time_seconds": exec_time
            }
        )
        await self.db.commit()

        return PersistentAnalysisResponse(
            id=analysis.id,
            organization_id=analysis.organization_id,
            client_id=analysis.client_id,
            client_name=client.name,
            client_code=client.client_code,
            dataset_id=analysis.dataset_id,
            dataset_filename=dataset.filename,
            user_id=analysis.user_id,
            model_name=analysis.model_name,
            optimal_threshold=analysis.optimal_threshold,
            execution_time_seconds=analysis.execution_time_seconds,
            status=analysis.status,
            validation_metrics=analysis.validation_metrics,
            test_metrics=analysis.test_metrics,
            fraud_statistics=analysis.fraud_statistics,
            risk_statistics=analysis.risk_statistics,
            category_breakdown=analysis.category_breakdown,
            empirical_findings=analysis.empirical_findings,
            recommendations=analysis.recommendations,
            global_feature_importance=analysis.global_feature_importance,
            created_at=analysis.created_at
        )
