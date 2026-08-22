"""Automated tests for Explainability, SHAP and Local Attributions."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from backend.app.services.ml.explainers import TransactionExplainer
from backend.app.schemas.explainability import LocalExplanation


class TestExplainability:

    def test_local_explanation_and_caching(self):
        np.random.seed(42)
        X = np.random.uniform(0, 10, size=(100, 5))
        y = (X[:, 0] > 5).astype(int)

        feature_names = ["feat_amount", "feat_distance", "feat_age", "feat_hour", "feat_category"]
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X, y)

        explainer = TransactionExplainer(model=model, feature_names=feature_names)

        tx_id = "tx_9999"
        row = X[0]
        raw_dict = {name: float(val) for name, val in zip(feature_names, row)}

        # First call: computes and returns is_cached=False
        exp1 = explainer.explain_transaction(
            transaction_id=tx_id,
            transformed_row=row,
            raw_features_dict=raw_dict,
            fraud_probability=0.85,
            top_k=3
        )

        assert isinstance(exp1, LocalExplanation)
        assert exp1.transaction_id == tx_id
        assert exp1.fraud_probability == 0.85
        assert exp1.risk_score == 85.0
        assert exp1.risk_band == "CRITICAL"
        assert exp1.is_cached is False
        assert len(exp1.positive_contributions) <= 3

        # Second call: returns cached result with is_cached=True
        exp2 = explainer.explain_transaction(
            transaction_id=tx_id,
            transformed_row=row,
            raw_features_dict=raw_dict,
            fraud_probability=0.85,
            top_k=3
        )

        assert exp2.is_cached is True
        assert exp2.transaction_id == tx_id
        assert exp2.risk_score == 85.0
