"""Comprehensive Fraud Model Evaluation Metrics for Sentinel AI.
Calculates PR-AUC, ROC-AUC, Recall, Precision, F1, FPR, FNR, Confusion Matrix,
and curve coordinate arrays from actual model predictions.
"""
from typing import List, Tuple, Dict, Any
import numpy as np
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    accuracy_score
)
from ...schemas.ml import CandidateModelMetrics, ConfusionMatrix, CurvePoint


class ModelEvaluator:
    """Evaluates fraud detection models across imbalanced classification metrics."""

    @classmethod
    def evaluate(
        cls,
        model_name: str,
        y_true: np.ndarray,
        y_prob: np.ndarray,
        threshold: float = 0.5
    ) -> CandidateModelMetrics:
        """
        Computes all verified imbalanced metrics at the specified threshold.
        """
        y_pred = (y_prob >= threshold).astype(int)

        prec = float(round(precision_score(y_true, y_pred, zero_division=0), 4))
        rec = float(round(recall_score(y_true, y_pred, zero_division=0), 4))
        f1 = float(round(f1_score(y_true, y_pred, zero_division=0), 4))
        acc = float(round(accuracy_score(y_true, y_pred), 4))

        # PR-AUC and ROC-AUC
        try:
            pr_auc = float(round(average_precision_score(y_true, y_prob), 4))
        except Exception:
            pr_auc = 0.0

        try:
            roc_auc = float(round(roc_auc_score(y_true, y_prob), 4))
        except Exception:
            roc_auc = 0.5

        # Confusion Matrix
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        fpr = float(round(fp / (fp + tn), 4)) if (fp + tn) > 0 else 0.0
        fnr = float(round(fn / (fn + tp), 4)) if (fn + tp) > 0 else 0.0

        # PR Curve points
        precisions, recalls, pr_thresh = precision_recall_curve(y_true, y_prob)
        step_pr = max(1, len(recalls) // 40)
        pr_curve = [
            CurvePoint(
                x=round(float(recalls[i]), 4),
                y=round(float(precisions[i]), 4),
                threshold=round(float(pr_thresh[i]), 4) if i < len(pr_thresh) else None
            )
            for i in range(0, len(recalls), step_pr)
        ]

        # ROC Curve points
        fpr_arr, tpr_arr, roc_thresh = roc_curve(y_true, y_prob)
        step_roc = max(1, len(fpr_arr) // 40)
        roc_curve_points = [
            CurvePoint(
                x=round(float(fpr_arr[i]), 4),
                y=round(float(tpr_arr[i]), 4),
                threshold=round(float(roc_thresh[i]), 4) if i < len(roc_thresh) else None
            )
            for i in range(0, len(fpr_arr), step_roc)
        ]

        return CandidateModelMetrics(
            model_name=model_name,
            precision=prec,
            recall=rec,
            f1=f1,
            pr_auc=pr_auc,
            roc_auc=roc_auc,
            false_positive_rate=fpr,
            false_negative_rate=fnr,
            accuracy=acc,
            confusion_matrix=ConfusionMatrix(
                true_positive=int(tp),
                false_positive=int(fp),
                true_negative=int(tn),
                false_negative=int(fn)
            ),
            pr_curve=pr_curve,
            roc_curve=roc_curve_points
        )
