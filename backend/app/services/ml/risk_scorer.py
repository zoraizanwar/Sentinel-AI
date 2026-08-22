"""Deterministic Risk Scoring Module for Sentinel AI.
Implements the transparent risk score formula directly derived from model fraud probability:
    risk_score = round(fraud_probability * 100, 2)
with standard enterprise risk bands:
    0.00 - 20.00   = LOW
    20.01 - 50.00  = MEDIUM
    50.01 - 80.00  = HIGH
    80.01 - 100.00 = CRITICAL

Notice: Tree ensemble classifiers (Random Forest, XGBoost) output tree leaf vote
distributions. These raw model probabilities are linearly scaled into a 0-100 risk score
without post-hoc statistical calibration (e.g. Platt scaling or isotonic regression).
"""
from typing import Union, Tuple, List
import numpy as np
import pandas as pd


class RiskScorer:
    """Deterministic, verified Risk Scoring Engine."""

    BAND_LOW = "LOW"
    BAND_MEDIUM = "MEDIUM"
    BAND_HIGH = "HIGH"
    BAND_CRITICAL = "CRITICAL"

    @classmethod
    def compute_risk_score(cls, fraud_probability: float) -> float:
        """
        Computes 0-100 risk score directly from model fraud probability.
        Strictly validates that probability is in [0.0, 1.0].
        """
        if fraud_probability is None or np.isnan(fraud_probability):
            raise ValueError("Fraud probability cannot be None or NaN.")

        if fraud_probability < 0.0 or fraud_probability > 1.0:
            raise ValueError(f"Fraud probability must be in [0.0, 1.0], got {fraud_probability}")

        score = round(float(fraud_probability) * 100.0, 2)
        # Ensure floating precision bounds
        return max(0.0, min(100.0, score))

    @classmethod
    def get_risk_band(cls, risk_score: float) -> str:
        """
        Maps a 0-100 risk score to its corresponding risk classification band:
            0.00 - 20.00  -> LOW
            20.01 - 50.00 -> MEDIUM
            50.01 - 80.00 -> HIGH
            80.01 - 100.0 -> CRITICAL
        """
        if risk_score is None or np.isnan(risk_score):
            raise ValueError("Risk score cannot be None or NaN.")

        if risk_score < 0.0 or risk_score > 100.0:
            raise ValueError(f"Risk score must be in [0.0, 100.0], got {risk_score}")

        if risk_score <= 20.0:
            return cls.BAND_LOW
        elif risk_score <= 50.0:
            return cls.BAND_MEDIUM
        elif risk_score <= 80.0:
            return cls.BAND_HIGH
        else:
            return cls.BAND_CRITICAL

    @classmethod
    def batch_score(
        cls,
        probabilities: Union[np.ndarray, List[float]]
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Vectorized computation of risk scores and risk bands for an array of probabilities.
        Returns (risk_scores_array, risk_bands_list).
        """
        probs = np.asarray(probabilities, dtype=float)
        if np.any(np.isnan(probs)):
            raise ValueError("Probabilities array contains NaN values.")
        if np.any((probs < 0.0) | (probs > 1.0)):
            raise ValueError("All probabilities must be strictly bounded in [0.0, 1.0].")

        scores = np.round(probs * 100.0, 2)

        conditions = [
            scores <= 20.0,
            (scores > 20.0) & (scores <= 50.0),
            (scores > 50.0) & (scores <= 80.0),
            scores > 80.0
        ]
        choices = [
            cls.BAND_LOW,
            cls.BAND_MEDIUM,
            cls.BAND_HIGH,
            cls.BAND_CRITICAL
        ]
        bands = np.select(conditions, choices, default=cls.BAND_LOW).tolist()
        return scores, bands

    @classmethod
    def score_dataframe(
        cls,
        df: pd.DataFrame,
        prob_col: str = "fraud_probability"
    ) -> pd.DataFrame:
        """
        Applies vectorized risk score and risk band calculation to an entire DataFrame.
        Adds 'risk_score' and 'risk_band' columns.
        """
        if prob_col not in df.columns:
            raise KeyError(f"Probability column '{prob_col}' not found in DataFrame.")

        scored_df = df.copy()
        scores, bands = cls.batch_score(scored_df[prob_col].values)
        scored_df["risk_score"] = scores
        scored_df["risk_band"] = bands
        return scored_df
