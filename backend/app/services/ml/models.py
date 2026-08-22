"""Candidate Fraud Detection Model Architectures & Selection Engine for Sentinel AI."""
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from .evaluator import ModelEvaluator
from .threshold import ThresholdOptimizer
from ...schemas.ml import (
    CandidateModelMetrics,
    SelectedModelDetails,
    ModelEvaluationSummary,
    FeatureImportanceItem
)

# Optional XGBoost import with safe degradation
try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except (ImportError, Exception):
    HAS_XGBOOST = False


class ModelTrainer:
    """Trains and compares candidate fraud detection models."""

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.trained_models: Dict[str, Any] = {}
        self.val_probabilities: Dict[str, np.ndarray] = {}

    def get_candidate_models(self, scale_pos_weight: float = 1.0) -> Dict[str, Any]:
        """Instantiates deterministic candidate models with balanced class strategies."""
        models = {
            "Logistic Regression": LogisticRegression(
                class_weight="balanced",
                random_state=self.random_state,
                max_iter=1000,
                C=1.0,
                solver="lbfgs"
            ),
            "Random Forest": RandomForestClassifier(
                n_estimators=100,
                max_depth=14,
                min_samples_split=10,
                min_samples_leaf=4,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1
            )
        }

        if HAS_XGBOOST:
            try:
                models["XGBoost"] = XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    scale_pos_weight=max(1.0, scale_pos_weight),
                    random_state=self.random_state,
                    n_jobs=-1,
                    eval_metric="logloss"
                )
            except Exception:
                pass

        return models

    def train_and_evaluate_candidates(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
        feature_names: List[str]
    ) -> Tuple[ModelEvaluationSummary, Any, str, float]:
        """
        Trains all candidate models on X_train/y_train, evaluates on X_val/y_val,
        optimizes threshold on validation set, and selects the winning model based on PR-AUC & F1.

        Returns:
            summary: ModelEvaluationSummary schema
            best_model: Trained model instance
            best_model_name: Identifier of winning model
            best_threshold: Frozen optimal threshold
        """
        pos_count = np.sum(y_train == 1)
        neg_count = np.sum(y_train == 0)
        imbalance_scale = float(neg_count / pos_count) if pos_count > 0 else 1.0

        candidate_configs = self.get_candidate_models(scale_pos_weight=imbalance_scale)
        metrics_list: List[CandidateModelMetrics] = []
        optimized_thresholds: Dict[str, float] = {}
        threshold_results: Dict[str, Any] = {}

        best_model_name = None
        best_pr_auc = -1.0
        best_f1 = -1.0

        for name, model in candidate_configs.items():
            # 1. Fit model strictly on training data
            model.fit(X_train, y_train)
            self.trained_models[name] = model

            # 2. Predict probabilities on validation data
            if hasattr(model, "predict_proba"):
                val_probs = model.predict_proba(X_val)[:, 1]
            elif hasattr(model, "decision_function"):
                decision = model.decision_function(X_val)
                val_probs = 1.0 / (1.0 + np.exp(-decision))
            else:
                val_probs = model.predict(X_val).astype(float)

            self.val_probabilities[name] = val_probs

            # 3. Optimize decision threshold on validation set
            opt_thresh, thresh_res, pr_curve = ThresholdOptimizer.optimize_threshold(
                y_true=y_val, y_prob=val_probs, objective="MAX_F1"
            )
            optimized_thresholds[name] = opt_thresh
            threshold_results[name] = thresh_res

            # 4. Evaluate imbalanced metrics at the optimized threshold
            candidate_metrics = ModelEvaluator.evaluate(
                model_name=name,
                y_true=y_val,
                y_prob=val_probs,
                threshold=opt_thresh
            )
            metrics_list.append(candidate_metrics)

            # 5. Selection Policy: Rank by PR-AUC primarily, then F1
            if (candidate_metrics.pr_auc > best_pr_auc) or (
                np.isclose(candidate_metrics.pr_auc, best_pr_auc, atol=0.005) and candidate_metrics.f1 > best_f1
            ):
                best_pr_auc = candidate_metrics.pr_auc
                best_f1 = candidate_metrics.f1
                best_model_name = name

        # Selected model details
        best_model = self.trained_models[best_model_name]
        best_thresh = optimized_thresholds[best_model_name]
        best_thresh_info = threshold_results[best_model_name]

        justification = (
            f"{best_model_name} selected as primary fraud detection model because it achieved the highest "
            f"validation PR-AUC ({best_pr_auc:.4f}) and F1 score ({best_f1:.4f}) at the optimized "
            f"operational threshold of {best_thresh:.4f}."
        )

        selected_details = SelectedModelDetails(
            model_name=best_model_name,
            justification=justification,
            selection_metric="PR-AUC",
            selection_value=best_pr_auc,
            optimal_threshold=best_thresh,
            threshold_methodology=best_thresh_info.methodology
        )

        # Global Feature Importance
        global_importance = self.extract_global_feature_importance(best_model, feature_names)

        summary = ModelEvaluationSummary(
            candidate_models=metrics_list,
            selected_model=selected_details,
            global_feature_importance=global_importance,
            is_xgboost_available=HAS_XGBOOST,
            validation_fraud_count=int(np.sum(y_val == 1)),
            validation_legit_count=int(np.sum(y_val == 0))
        )

        return summary, best_model, best_model_name, best_thresh

    def extract_global_feature_importance(
        self, model: Any, feature_names: List[str]
    ) -> List[FeatureImportanceItem]:
        """Extracts feature importance weights from the fitted model."""
        importances = None

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            # Use absolute magnitude of coefficients for linear models
            importances = np.abs(model.coef_[0])

        if importances is None or len(importances) != len(feature_names):
            return []

        # Normalize to sum to 1.0
        total = np.sum(importances)
        norm_importances = (importances / total) if total > 0 else importances

        # Sort descending
        sorted_indices = np.argsort(norm_importances)[::-1]
        items = []
        for rank, idx in enumerate(sorted_indices, start=1):
            items.append(FeatureImportanceItem(
                feature_name=feature_names[idx],
                importance=float(round(norm_importances[idx], 4)),
                rank=rank
            ))
        return items
