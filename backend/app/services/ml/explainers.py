"""Explainability & SHAP Attribution Engine for Sentinel AI.
Provides global feature importance and on-demand local SHAP explanations
with session-level caching for fast investigator inspection.
"""
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

from ...schemas.explainability import LocalExplanation, SHAPContribution
from .risk_scorer import RiskScorer

# Optional SHAP import with safe fallback
try:
    import shap
    HAS_SHAP = True
except (ImportError, Exception):
    HAS_SHAP = False


class TransactionExplainer:
    """
    Computes and caches on-demand local SHAP feature attributions
    for suspicious and investigated transactions.
    """

    def __init__(self, model: Any, feature_names: List[str], background_sample: Optional[np.ndarray] = None):
        self.model = model
        self.feature_names = feature_names
        self.background_sample = background_sample
        self.explainer: Optional[Any] = None
        self.shap_cache: Dict[str, LocalExplanation] = {}
        self._init_explainer()

    def _init_explainer(self) -> None:
        """Initializes the appropriate SHAP explainer based on model family."""
        if not HAS_SHAP:
            return

        try:
            model_class_name = self.model.__class__.__name__
            if "Forest" in model_class_name or "XGB" in model_class_name or "Tree" in model_class_name:
                self.explainer = shap.TreeExplainer(self.model)
            elif "Logistic" in model_class_name or "Linear" in model_class_name:
                if self.background_sample is not None:
                    # Use a small background summary (max 50 samples)
                    sample = self.background_sample[:50]
                    self.explainer = shap.LinearExplainer(self.model, sample)
                else:
                    self.explainer = shap.Explainer(self.model)
            else:
                self.explainer = shap.Explainer(self.model)
        except Exception:
            self.explainer = None

    def explain_transaction(
        self,
        transaction_id: str,
        transformed_row: np.ndarray,
        raw_features_dict: Dict[str, Any],
        fraud_probability: float,
        top_k: int = 5
    ) -> LocalExplanation:
        """
        Computes or retrieves from cache the local SHAP explanation for a transaction.
        """
        # 1. Check cache first
        if transaction_id in self.shap_cache:
            cached = self.shap_cache[transaction_id].model_copy()
            cached.is_cached = True
            return cached

        risk_score = RiskScorer.compute_risk_score(fraud_probability)
        risk_band = RiskScorer.get_risk_band(risk_score)

        # 2. Compute SHAP values
        pos_contribs: List[SHAPContribution] = []
        neg_contribs: List[SHAPContribution] = []
        base_val = 0.5
        method_name = "TreeExplainer" if self.explainer is not None else "FeatureMagnitudeHeuristic"

        if self.explainer is not None:
            try:
                row_2d = transformed_row.reshape(1, -1)
                shap_values = self.explainer.shap_values(row_2d)

                # Handle binary classification output formats
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    # Class 1 (fraud) shap values
                    shap_vec = np.array(shap_values[1]).flatten()
                elif isinstance(shap_values, np.ndarray):
                    if shap_values.ndim == 3 and shap_values.shape[2] == 2:
                        shap_vec = shap_values[0, :, 1]
                    elif shap_values.ndim == 2:
                        shap_vec = shap_values[0]
                    else:
                        shap_vec = shap_values.flatten()
                elif hasattr(shap_values, "values"):
                    val_arr = shap_values.values
                    if val_arr.ndim == 3:
                        shap_vec = val_arr[0, :, 1]
                    else:
                        shap_vec = val_arr[0]
                else:
                    shap_vec = np.array(shap_values).flatten()

                # Extract base expected value
                if hasattr(self.explainer, "expected_value"):
                    exp_val = self.explainer.expected_value
                    if isinstance(exp_val, (list, np.ndarray)) and len(exp_val) > 1:
                        base_val = float(round(exp_val[1], 4))
                    else:
                        base_val = float(round(float(exp_val), 4))

                pos_contribs, neg_contribs = self._rank_shap_contributions(
                    shap_vec, transformed_row, raw_features_dict, top_k=top_k
                )
            except Exception:
                # Fallback to feature magnitude if SHAP computation encounters an edge case
                pos_contribs, neg_contribs = self._heuristic_fallback(transformed_row, raw_features_dict, top_k=top_k)
                method_name = "FeatureMagnitudeFallback"
        else:
            pos_contribs, neg_contribs = self._heuristic_fallback(transformed_row, raw_features_dict, top_k=top_k)
            method_name = "FeatureImportanceHeuristic"

        explanation = LocalExplanation(
            transaction_id=transaction_id,
            fraud_probability=fraud_probability,
            risk_score=risk_score,
            risk_band=risk_band,
            base_value=base_val,
            positive_contributions=pos_contribs,
            negative_contributions=neg_contribs,
            method=method_name,
            is_cached=False
        )

        # Cache result
        self.shap_cache[transaction_id] = explanation
        return explanation

    def _rank_shap_contributions(
        self,
        shap_vec: np.ndarray,
        transformed_row: np.ndarray,
        raw_features_dict: Dict[str, Any],
        top_k: int = 5
    ) -> Tuple[List[SHAPContribution], List[SHAPContribution]]:
        """Ranks positive (risk-increasing) and negative (risk-decreasing) SHAP factors."""
        pos_list = []
        neg_list = []

        for i, (name, val, shap_val) in enumerate(zip(self.feature_names, transformed_row, shap_vec)):
            raw_val = raw_features_dict.get(name, val)
            s_val = float(round(shap_val, 4))
            
            if s_val > 0:
                pos_list.append((s_val, name, raw_val, s_val))
            elif s_val < 0:
                neg_list.append((abs(s_val), name, raw_val, s_val))

        # Sort descending by magnitude
        pos_list.sort(key=lambda x: x[0], reverse=True)
        neg_list.sort(key=lambda x: x[0], reverse=True)

        pos_contribs = [
            SHAPContribution(
                feature_name=item[1],
                feature_value=str(item[2]),
                shap_value=item[3],
                contribution_type="RISK_INCREASING",
                human_explanation=self._generate_explanation_text(item[1], item[2], item[3], is_positive=True)
            )
            for item in pos_list[:top_k]
        ]

        neg_contribs = [
            SHAPContribution(
                feature_name=item[1],
                feature_value=str(item[2]),
                shap_value=item[3],
                contribution_type="RISK_DECREASING",
                human_explanation=self._generate_explanation_text(item[1], item[2], item[3], is_positive=False)
            )
            for item in neg_list[:top_k]
        ]

        return pos_contribs, neg_contribs

    def _heuristic_fallback(
        self,
        transformed_row: np.ndarray,
        raw_features_dict: Dict[str, Any],
        top_k: int = 5
    ) -> Tuple[List[SHAPContribution], List[SHAPContribution]]:
        """Fallback attribution based on non-zero transformed feature values."""
        pos_contribs = []
        for i, name in enumerate(self.feature_names[:top_k]):
            val = transformed_row[i] if i < len(transformed_row) else 0.0
            raw_val = raw_features_dict.get(name, val)
            pos_contribs.append(
                SHAPContribution(
                    feature_name=name,
                    feature_value=str(raw_val),
                    shap_value=float(round(val, 4)),
                    contribution_type="RISK_INCREASING",
                    human_explanation=f"Feature '{name}' (value: {raw_val}) contributed to model decision."
                )
            )
        return pos_contribs, []

    def _generate_explanation_text(self, feature_name: str, value: Any, shap_val: float, is_positive: bool) -> str:
        """Translates technical SHAP weights into clear domain explanations."""
        direction = "increased" if is_positive else "decreased"
        
        if "distance_km" in feature_name:
            return f"Geographic distance of {value} km {direction} fraud risk score by {abs(shap_val):.3f}."
        elif "log_amount" in feature_name or "amt" in feature_name:
            return f"Transaction amount of ${value} {direction} fraud risk score by {abs(shap_val):.3f}."
        elif "hour_of_day" in feature_name or "night" in feature_name:
            return f"Transaction timing ({value}:00 hours) {direction} fraud risk score by {abs(shap_val):.3f}."
        elif "customer_age" in feature_name:
            return f"Customer age ({value} years) {direction} risk score by {abs(shap_val):.3f}."
        elif "category" in feature_name:
            cat_name = feature_name.replace("category_", "").replace("cat__category_", "")
            return f"Merchant category '{cat_name}' {direction} risk score by {abs(shap_val):.3f}."
        else:
            return f"Feature '{feature_name}' (value: {value}) {direction} risk score by {abs(shap_val):.3f}."
