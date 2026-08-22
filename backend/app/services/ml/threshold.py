"""Classification Threshold Optimization Module for Sentinel AI.
Dynamically searches the Precision-Recall curve on the validation split
to identify the optimal decision threshold for imbalanced fraud classification.
"""
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score
from ...schemas.ml import ThresholdOptimizationResult, CurvePoint


class ThresholdOptimizer:
    """Optimizes decision threshold on validation predictions."""

    @classmethod
    def optimize_threshold(
        cls,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        objective: str = "MAX_F1",
        beta: float = 1.0
    ) -> Tuple[float, ThresholdOptimizationResult, List[CurvePoint]]:
        """
        Calculates the Precision-Recall curve and finds the threshold maximizing F1 (or F_beta).
        Only call this using validation data, never test data.
        """
        precisions, recalls, thresholds = precision_recall_curve(y_true, y_prob)

        # Avoid zero division
        f_scores = []
        for p, r in zip(precisions[:-1], recalls[:-1]):
            if (p + r) > 0:
                # F_beta score
                f = (1 + beta**2) * (p * r) / ((beta**2 * p) + r)
            else:
                f = 0.0
            f_scores.append(f)

        f_scores = np.array(f_scores)
        best_idx = int(np.argmax(f_scores))
        
        best_threshold = float(round(thresholds[best_idx], 4)) if len(thresholds) > 0 else 0.5
        # Ensure threshold bounds
        best_threshold = max(0.01, min(0.99, best_threshold))

        # Calculate exact metrics at optimal threshold
        y_pred = (y_prob >= best_threshold).astype(int)
        val_precision = float(round(precision_score(y_true, y_pred, zero_division=0), 4))
        val_recall = float(round(recall_score(y_true, y_pred, zero_division=0), 4))
        val_f1 = float(round(f1_score(y_true, y_pred, zero_division=0), 4))

        methodology = (
            f"Precision-Recall curve optimization on validation set maximizing F{beta:g}-score. "
            f"Selected threshold {best_threshold:.4f} achieves Precision: {val_precision:.4f}, "
            f"Recall: {val_recall:.4f}, F1: {val_f1:.4f}."
        )

        result = ThresholdOptimizationResult(
            optimal_threshold=best_threshold,
            methodology=methodology,
            validation_precision=val_precision,
            validation_recall=val_recall,
            validation_f1=val_f1,
            selection_objective=f"Maximize F{beta:g}"
        )

        # Sample PR curve points (downsample to ~50 points for clean UI transmission)
        step = max(1, len(thresholds) // 50)
        pr_curve_points = [
            CurvePoint(x=round(float(recalls[i]), 4), y=round(float(precisions[i]), 4), threshold=round(float(thresholds[i]), 4))
            for i in range(0, len(thresholds), step)
        ]

        return best_threshold, result, pr_curve_points
