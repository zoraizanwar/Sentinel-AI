"""Automated tests verifying strict data leakage prevention in Sentinel AI."""
import pytest
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from backend.app.services.ml.feature_engineering import FeatureEngineeringPipeline
from backend.app.services.ml.preprocessor import LeakFreePreprocessor


class TestLeakagePrevention:

    def test_preprocessor_fits_on_train_only(self, sample_valid_df):
        """Verifies that scalers and encoders are fitted strictly on training data."""
        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target = fe.extract_features(sample_valid_df)

        # Split 75/25 train/test
        X_train, X_val, y_train, y_val = train_test_split(
            features_df, target, test_size=0.25, random_state=42, stratify=target
        )

        preprocessor = LeakFreePreprocessor()
        # Assert not fitted initially
        assert preprocessor.is_fitted is False
        with pytest.raises(RuntimeError):
            preprocessor.transform(X_val)

        # Fit on train only
        X_train_trans = preprocessor.fit_transform(X_train)
        assert preprocessor.is_fitted is True
        assert X_train_trans.shape[0] == len(X_train)

        # Transform validation without re-fitting
        X_val_trans = preprocessor.transform(X_val)
        assert X_val_trans.shape[0] == len(X_val)
        assert X_val_trans.shape[1] == X_train_trans.shape[1]

    def test_excluded_identifiers_and_pii_not_in_features(self, sample_valid_df):
        """Verifies that trans_num, first, last, street, and Unnamed: 0 are excluded from ML features."""
        # Add PII columns to sample
        df_with_pii = sample_valid_df.copy()
        df_with_pii["Unnamed: 0"] = range(len(df_with_pii))
        df_with_pii["first"] = ["John"] * len(df_with_pii)
        df_with_pii["last"] = ["Doe"] * len(df_with_pii)
        df_with_pii["street"] = ["123 Main St"] * len(df_with_pii)
        df_with_pii["merchant"] = ["fraud_test_merch"] * len(df_with_pii)
        df_with_pii["job"] = ["Engineer"] * len(df_with_pii)

        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target = fe.extract_features(df_with_pii)

        # Assert excluded from ML features
        for excluded in ["Unnamed: 0", "trans_num", "first", "last", "street", "cc_num", "merchant", "job"]:
            assert excluded not in features_df.columns

        # Assert retained in metadata
        assert "trans_num" in metadata_df.columns
        assert "first" in metadata_df.columns
        assert "last" in metadata_df.columns
        assert "street" in metadata_df.columns

    def test_target_isolated_without_leakage(self, sample_valid_df):
        """Verifies that the target column is completely removed from the feature matrix."""
        fe = FeatureEngineeringPipeline()
        features_df, metadata_df, target = fe.extract_features(sample_valid_df)

        assert "is_fraud" not in features_df.columns
        assert "is_fraud" not in metadata_df.columns
        assert target is not None
        assert len(target) == len(features_df)
