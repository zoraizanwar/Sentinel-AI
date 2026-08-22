"""Automated tests for Classification Threshold Optimization on PR Curves."""
import numpy as np
from backend.app.services.ml.threshold import ThresholdOptimizer
from backend.app.schemas.ml import ThresholdOptimizationResult


class TestThresholdOptimization:

    def test_threshold_optimization_on_synthetic_probs(self):
        np.random.seed(42)
        n = 200
        # 10 frauds out of 200 (5%)
        y_true = np.array([1] * 10 + [0] * 190)
        # Probabilities: frauds have higher prob, legit lower
        y_prob = np.concatenate([
            np.random.uniform(0.4, 0.9, size=10),
            np.random.uniform(0.0, 0.3, size=190)
        ])

        threshold, res, pr_curve = ThresholdOptimizer.optimize_threshold(y_true, y_prob, objective="MAX_F1")

        assert 0.0 < threshold < 1.0
        assert isinstance(res, ThresholdOptimizationResult)
        assert res.optimal_threshold == threshold
        assert res.validation_f1 > 0.5
        assert len(pr_curve) > 0
        assert all(0.0 <= pt.x <= 1.0 and 0.0 <= pt.y <= 1.0 for pt in pr_curve)

    def test_threshold_never_fixed_to_default(self):
        # Even with severe skew, optimizer finds an empirical threshold
        y_true = np.array([1] * 5 + [0] * 95)
        y_prob = np.concatenate([
            np.random.uniform(0.6, 0.95, size=5),
            np.random.uniform(0.01, 0.2, size=95)
        ])

        threshold, res, _ = ThresholdOptimizer.optimize_threshold(y_true, y_prob)
        assert threshold > 0.2
        assert threshold < 0.95
