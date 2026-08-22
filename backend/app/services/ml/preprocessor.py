"""Leak-Free Tabular Preprocessing Pipeline for Sentinel AI.
Ensures that all scalers, imputers, and encoders are fitted strictly on training data
and applied to validation/test sets via transformation only.
"""
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, RobustScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline


class LeakFreePreprocessor:
    """
    Scikit-learn based ColumnTransformer pipeline fitted strictly on training data.
    Provides verified feature names mapping for explainability and model inspection.
    """

    def __init__(self, high_cardinality_threshold: int = 50):
        self.high_cardinality_threshold = high_cardinality_threshold
        self.transformer: Optional[ColumnTransformer] = None
        self.numeric_features: List[str] = []
        self.categorical_features: List[str] = []
        self.output_feature_names: List[str] = []
        self.is_fitted: bool = False

    def _identify_column_types(self, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """Identifies numeric and categorical columns from the feature matrix."""
        numeric_cols = []
        categorical_cols = []

        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)

        return numeric_cols, categorical_cols

    def fit(self, X_train: pd.DataFrame) -> "LeakFreePreprocessor":
        """
        Fits scalers, imputers, and encoders strictly on the training partition.
        Never call this on validation or test sets.
        """
        self.numeric_features, self.categorical_features = self._identify_column_types(X_train)

        # Numeric transformer pipeline: Impute median + RobustScaler (resistant to financial outliers)
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler())
        ])

        # Categorical transformer pipeline: Impute most frequent + OneHotEncoder
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
        ])

        transformers = []
        if self.numeric_features:
            transformers.append(("num", numeric_pipeline, self.numeric_features))
        if self.categorical_features:
            transformers.append(("cat", categorical_pipeline, self.categorical_features))

        self.transformer = ColumnTransformer(
            transformers=transformers,
            remainder="drop"
        )

        self.transformer.fit(X_train)
        self.is_fitted = True
        self._build_feature_names()
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Applies fitted transformations to unseen validation or test features.
        Does not re-fit.
        """
        if not self.is_fitted or self.transformer is None:
            raise RuntimeError("LeakFreePreprocessor must be fitted on training data before calling transform().")
        return self.transformer.transform(X)

    def fit_transform(self, X_train: pd.DataFrame) -> np.ndarray:
        """Convenience method for training data only."""
        return self.fit(X_train).transform(X_train)

    def _build_feature_names(self) -> None:
        """Builds clean, human-interpretable feature names for all output dimensions."""
        feature_names = []
        if self.transformer is None:
            return

        for name, trans, cols in self.transformer.transformers_:
            if name == "num":
                feature_names.extend(cols)
            elif name == "cat":
                encoder = trans.named_steps["encoder"]
                cat_names = encoder.get_feature_names_out(cols)
                # Clean up names (e.g., category_grocery_pos)
                feature_names.extend([str(c) for c in cat_names])
                
        self.output_feature_names = feature_names

    def get_feature_names(self) -> List[str]:
        """Returns the list of transformed feature names."""
        return self.output_feature_names
