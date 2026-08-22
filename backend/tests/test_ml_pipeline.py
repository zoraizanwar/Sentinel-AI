"""End-to-End Unit & Integration Tests for the ML Pipeline."""
import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from backend.app.services.ml.feature_engineering import FeatureEngineeringPipeline
from backend.app.services.ml.preprocessor import LeakFreePreprocessor
from backend.app.services.ml.models import ModelTrainer
from backend.app.services.ml.risk_scorer import RiskScorer
from backend.app.schemas.ml import ModelEvaluationSummary


class TestMLPipeline:

    def test_end_to_end_ml_pipeline_execution(self, sample_valid_df):
        # 1. Feature Engineering
        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target = fe.extract_features(sample_valid_df)

        assert len(features_df) == len(sample_valid_df)
        assert len(metadata_df) == len(sample_valid_df)
        assert "is_fraud" not in features_df.columns

        # 2. Stratified Train / Validation Split
        X_train, X_val, y_train, y_val = train_test_split(
            features_df, target, test_size=0.30, random_state=42, stratify=target
        )

        # 3. Leak-free Preprocessing
        preprocessor = LeakFreePreprocessor()
        X_train_proc = preprocessor.fit_transform(X_train)
        X_val_proc = preprocessor.transform(X_val)

        assert X_train_proc.shape[1] == X_val_proc.shape[1]
        feature_names = preprocessor.get_feature_names()
        assert len(feature_names) == X_train_proc.shape[1]

        # 4. Model Training & Comparison
        trainer = ModelTrainer(random_state=42)
        summary, best_model, best_name, opt_thresh = trainer.train_and_evaluate_candidates(
            X_train=X_train_proc,
            y_train=y_train.values,
            X_val=X_val_proc,
            y_val=y_val.values,
            feature_names=feature_names
        )

        assert isinstance(summary, ModelEvaluationSummary)
        assert len(summary.candidate_models) >= 2  # At least LogReg and RandomForest
        assert summary.selected_model.model_name == best_name
        assert 0.0 < opt_thresh < 1.0
        assert len(summary.global_feature_importance) > 0

        # 5. Batch Predictions & Risk Scoring
        val_probs = trainer.val_probabilities[best_name]
        scores, bands = RiskScorer.batch_score(val_probs)

        assert len(scores) == len(val_probs)
        assert len(bands) == len(val_probs)
        assert all(b in ["LOW", "MEDIUM", "HIGH", "CRITICAL"] for b in bands)
