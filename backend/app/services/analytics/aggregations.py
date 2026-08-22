"""Statistical Aggregations & Risk Pattern Analytics Engine for Sentinel AI.
All metrics are derived strictly through deterministic calculations on the dataset
and model predictions with zero data fabrication.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from ...schemas.analysis import (
    FraudStatistics,
    RiskStatistics,
    RiskDistributionSummary,
    CategoricalBreakdown,
    RiskPattern
)


class AnalyticsEngine:
    """Computes verified statistical summaries, categorical breakdowns, and risk distributions."""

    @classmethod
    def compute_fraud_statistics(
        cls, df: pd.DataFrame, target_col: str, amount_col: Optional[str] = "amt"
    ) -> FraudStatistics:
        """Calculates total counts, fraud proportions, and monetary loss exposure."""
        total_tx = len(df)
        if total_tx == 0:
            return FraudStatistics(
                total_transactions=0,
                fraud_count=0,
                legitimate_count=0,
                fraud_rate_percentage=0.0,
                total_volume_usd=0.0,
                fraud_volume_usd=0.0,
                fraud_loss_percentage=0.0
            )

        y = df[target_col].astype(int)
        fraud_count = int(np.sum(y == 1))
        legit_count = int(np.sum(y == 0))
        fraud_pct = round((fraud_count / total_tx) * 100.0, 4)

        total_vol = 0.0
        fraud_vol = 0.0
        loss_pct = 0.0

        if amount_col and amount_col in df.columns:
            amt_series = df[amount_col].fillna(0.0).clip(lower=0.0)
            total_vol = float(round(amt_series.sum(), 2))
            fraud_vol = float(round(amt_series[y == 1].sum(), 2))
            loss_pct = round((fraud_vol / total_vol) * 100.0, 4) if total_vol > 0 else 0.0

        return FraudStatistics(
            total_transactions=total_tx,
            fraud_count=fraud_count,
            legitimate_count=legit_count,
            fraud_rate_percentage=fraud_pct,
            total_volume_usd=total_vol,
            fraud_volume_usd=fraud_vol,
            fraud_loss_percentage=loss_pct
        )

    @classmethod
    def compute_risk_statistics(cls, risk_scores: np.ndarray, risk_bands: List[str]) -> RiskStatistics:
        """Calculates exact risk tier counts and summary statistics."""
        total = len(risk_scores)
        if total == 0:
            return RiskStatistics(
                low_risk_count=0, low_risk_pct=0.0,
                medium_risk_count=0, medium_risk_pct=0.0,
                high_risk_count=0, high_risk_pct=0.0,
                critical_risk_count=0, critical_risk_pct=0.0,
                mean_risk_score=0.0, median_risk_score=0.0
            )

        band_series = pd.Series(risk_bands)
        counts = band_series.value_counts().to_dict()

        low = counts.get("LOW", 0)
        med = counts.get("MEDIUM", 0)
        high = counts.get("HIGH", 0)
        crit = counts.get("CRITICAL", 0)

        return RiskStatistics(
            low_risk_count=low,
            low_risk_pct=round((low / total) * 100.0, 2),
            medium_risk_count=med,
            medium_risk_pct=round((med / total) * 100.0, 2),
            high_risk_count=high,
            high_risk_pct=round((high / total) * 100.0, 2),
            critical_risk_count=crit,
            critical_risk_pct=round((crit / total) * 100.0, 2),
            mean_risk_score=float(round(np.mean(risk_scores), 2)),
            median_risk_score=float(round(np.median(risk_scores), 2))
        )

    @classmethod
    def compute_risk_distribution(
        cls, risk_scores: np.ndarray, y_true: Optional[np.ndarray] = None
    ) -> RiskDistributionSummary:
        """Computes 10-point histogram bins (0-10, 10-20, ... 90-100)."""
        bin_labels = [
            "0-10", "10-20", "20-30", "30-40", "40-50",
            "50-60", "60-70", "70-80", "80-90", "90-100"
        ]
        bins = np.linspace(0, 100, 11)
        counts, _ = np.histogram(risk_scores, bins=bins)

        fraud_counts = []
        if y_true is not None and len(y_true) == len(risk_scores):
            for i in range(len(bins) - 1):
                mask = (risk_scores >= bins[i]) & (risk_scores <= bins[i+1] if i == len(bins)-2 else risk_scores < bins[i+1])
                f_count = int(np.sum(y_true[mask] == 1))
                fraud_counts.append(f_count)
        else:
            fraud_counts = [0] * len(bin_labels)

        return RiskDistributionSummary(
            score_bins=bin_labels,
            counts=[int(c) for c in counts],
            fraud_counts_per_bin=fraud_counts
        )

    @classmethod
    def compute_categorical_breakdowns(
        cls, df: pd.DataFrame, target_col: str, category_col: str = "category", amount_col: str = "amt"
    ) -> Dict[str, CategoricalBreakdown]:
        """Calculates volume, fraud counts, and fraud rates across merchant categories."""
        breakdowns = {}
        if category_col not in df.columns or target_col not in df.columns:
            return breakdowns

        y = df[target_col].astype(int)
        grouped = df.groupby(category_col)

        for cat_name, group in grouped:
            cat_str = str(cat_name)
            t_count = len(group)
            f_count = int((group[target_col] == 1).sum())
            f_rate = round((f_count / t_count) * 100.0, 4) if t_count > 0 else 0.0

            total_vol = 0.0
            fraud_vol = 0.0
            if amount_col in group.columns:
                total_vol = float(round(group[amount_col].sum(), 2))
                fraud_vol = float(round(group[group[target_col] == 1][amount_col].sum(), 2))

            breakdowns[cat_str] = CategoricalBreakdown(
                category_name=cat_str,
                total_count=t_count,
                fraud_count=f_count,
                fraud_rate_percentage=f_rate,
                total_volume_usd=total_vol,
                fraud_volume_usd=fraud_vol
            )

        return breakdowns

    @classmethod
    def detect_risk_patterns(
        cls, df: pd.DataFrame, target_col: str, amount_col: str = "amt"
    ) -> List[RiskPattern]:
        """Identifies verified risk patterns (e.g. night-time velocity, high-amount anomalies)."""
        patterns = []
        if len(df) == 0 or target_col not in df.columns:
            return patterns

        y = df[target_col].astype(int)
        baseline_rate = (y == 1).mean() * 100.0

        # Pattern 1: Night hours (23:00 - 06:00)
        if "trans_date_trans_time" in df.columns:
            dt = pd.to_datetime(df["trans_date_trans_time"], errors="coerce")
            night_mask = dt.dt.hour.isin([0, 1, 2, 3, 4, 5, 23])
            night_count = int(night_mask.sum())
            if night_count > 0:
                night_fraud_rate = float(round((df.loc[night_mask, target_col] == 1).mean() * 100.0, 3))
                if night_fraud_rate > baseline_rate:
                    patterns.append(RiskPattern(
                        pattern_name="Off-Hours Night Velocity Spike",
                        description=f"Transactions between 23:00 and 06:00 exhibited an elevated fraud rate of {night_fraud_rate:.2f}% compared with baseline ({baseline_rate:.2f}%).",
                        affected_count=night_count,
                        fraud_rate_percentage=night_fraud_rate,
                        severity="HIGH"
                    ))

        # Pattern 2: High Amount Outliers (> 5x mean amount)
        if amount_col in df.columns:
            amt_mean = df[amount_col].mean()
            high_amt_mask = df[amount_col] > (5 * amt_mean)
            high_count = int(high_amt_mask.sum())
            if high_count > 0:
                high_fraud_rate = float(round((df.loc[high_amt_mask, target_col] == 1).mean() * 100.0, 3))
                patterns.append(RiskPattern(
                    pattern_name="High-Value Transaction Concentration",
                    description=f"Transactions exceeding $ {5*amt_mean:.2f} (5x baseline mean) had a {high_fraud_rate:.2f}% fraud rate across {high_count:,} events.",
                    affected_count=high_count,
                    fraud_rate_percentage=high_fraud_rate,
                    severity="CRITICAL" if high_fraud_rate > 10.0 else "MEDIUM"
                ))

        return patterns
