"""Domain Feature Engineering Pipeline for Sentinel AI.
Extracts domain-grounded financial, temporal, age, and geographic distance signals
without causing target or future-information leakage.
"""
import numpy as np
import pandas as pd
from typing import Tuple, List, Dict, Any, Optional


def haversine_distance_km(
    lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    """
    Vectorized Haversine distance formula to compute great-circle distance
    in kilometers between cardholder residential location and merchant terminal.
    """
    R = 6371.0  # Earth's radius in kilometers
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)

    a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    a = np.clip(a, 0.0, 1.0)
    c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
    return R * c


class FeatureEngineeringPipeline:
    """
    Engineers tabular features from raw credit card transaction data.
    Preserves transaction metadata (trans_num, cc_num, PII, merchant names, jobs) in a separate DataFrame
    and ensures zero target leakage.
    """

    # High-cardinality and PII columns excluded from direct dense ML matrix
    EXCLUDED_METADATA_COLS = [
        "Unnamed: 0", "trans_num", "first", "last", "street", "merchant", "job", "city", "zip"
    ]

    def __init__(self):
        pass

    def extract_features(
        self, df: pd.DataFrame, is_training: bool = False
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.Series]]:
        """
        Processes the input DataFrame, generates engineered features, separates metadata,
        and extracts the ground truth target if available.

        Returns:
            features_df: Clean numeric and categorical feature matrix for ML.
            metadata_df: Transaction IDs, customer details, timestamps for investigation/UI.
            target_series: Binary fraud target series (if present).
        """
        work_df = df.copy()

        # 1. Extract and isolate target
        target_series = None
        for cand in ["is_fraud", "isFraud", "Class", "class", "target"]:
            if cand in work_df.columns:
                target_series = work_df[cand].astype(int)
                work_df = work_df.drop(columns=[cand])
                break

        # 2. Extract and preserve metadata
        meta_cols = [c for c in self.EXCLUDED_METADATA_COLS if c in work_df.columns]
        if "trans_num" in work_df.columns:
            metadata_df = work_df[meta_cols].copy()
        else:
            metadata_df = pd.DataFrame({"trans_num": [f"tx_{i}" for i in range(len(work_df))]})
            for c in meta_cols:
                if c != "trans_num" and c in work_df.columns:
                    metadata_df[c] = work_df[c]

        # Drop index column if present
        if "Unnamed: 0" in work_df.columns:
            work_df = work_df.drop(columns=["Unnamed: 0"])

        # 3. Temporal Feature Engineering
        if "trans_date_trans_time" in work_df.columns:
            dt_series = pd.to_datetime(work_df["trans_date_trans_time"], errors="coerce")
            work_df["hour_of_day"] = dt_series.dt.hour.fillna(12).astype(int)
            work_df["day_of_week"] = dt_series.dt.dayofweek.fillna(0).astype(int)
            work_df["month"] = dt_series.dt.month.fillna(1).astype(int)
            work_df["is_weekend"] = work_df["day_of_week"].isin([5, 6]).astype(int)
            work_df["is_night_hours"] = work_df["hour_of_day"].isin([0, 1, 2, 3, 4, 5, 23]).astype(int)
        else:
            work_df["hour_of_day"] = 12
            work_df["day_of_week"] = 0
            work_df["month"] = 1
            work_df["is_weekend"] = 0
            work_df["is_night_hours"] = 0

        # 4. Demographic Age Feature Engineering (relative to transaction timestamp)
        if "dob" in work_df.columns and "trans_date_trans_time" in work_df.columns:
            dob_series = pd.to_datetime(work_df["dob"], errors="coerce")
            dt_series = pd.to_datetime(work_df["trans_date_trans_time"], errors="coerce")
            age_years = (dt_series - dob_series).dt.days / 365.25
            work_df["customer_age_years"] = age_years.fillna(45.0).clip(18.0, 100.0).round(1)
        else:
            work_df["customer_age_years"] = 45.0

        # 5. Geographic Distance Feature Engineering (Haversine km)
        geo_cols = ["lat", "long", "merch_lat", "merch_long"]
        if all(c in work_df.columns for c in geo_cols):
            work_df["distance_km"] = haversine_distance_km(
                work_df["lat"].values,
                work_df["long"].values,
                work_df["merch_lat"].values,
                work_df["merch_long"].values,
            ).round(2)
        else:
            work_df["distance_km"] = 0.0

        # 6. Monetary Signal Transformation
        if "amt" in work_df.columns:
            work_df["log_amount"] = np.log1p(work_df["amt"].clip(lower=0.0)).round(4)
        else:
            work_df["amt"] = 0.0
            work_df["log_amount"] = 0.0

        # 7. Drop raw unneeded/redundant raw text and high-cardinality PII columns from ML matrix
        drop_from_ml = [
            "trans_date_trans_time",
            "unix_time",
            "dob",
            "trans_num",
            "cc_num",
            "first",
            "last",
            "street",
            "merchant",
            "job",
            "city",
            "zip",
            "lat",
            "long",
            "merch_lat",
            "merch_long",
        ]
        features_df = work_df.drop(columns=[c for c in drop_from_ml if c in work_df.columns])

        return features_df, metadata_df, target_series
