"""Automated tests for Risk Scoring Engine and deterministic Risk Bands."""
import pytest
import numpy as np
from backend.app.services.ml.risk_scorer import RiskScorer


class TestRiskScoring:

    @pytest.mark.parametrize(
        "prob, expected_score, expected_band",
        [
            (0.00, 0.0, "LOW"),
            (0.15, 15.0, "LOW"),
            (0.20, 20.0, "LOW"),
            (0.205, 20.5, "MEDIUM"),
            (0.21, 21.0, "MEDIUM"),
            (0.35, 35.0, "MEDIUM"),
            (0.50, 50.0, "MEDIUM"),
            (0.501, 50.1, "HIGH"),
            (0.51, 51.0, "HIGH"),
            (0.75, 75.0, "HIGH"),
            (0.80, 80.0, "HIGH"),
            (0.805, 80.5, "CRITICAL"),
            (0.81, 81.0, "CRITICAL"),
            (0.999, 99.9, "CRITICAL"),
            (1.00, 100.0, "CRITICAL"),
        ]
    )
    def test_risk_score_and_band_exact_mapping(self, prob, expected_score, expected_band):
        score = RiskScorer.compute_risk_score(prob)
        band = RiskScorer.get_risk_band(score)

        assert score == expected_score
        assert band == expected_band

    def test_invalid_probabilities_raise_error(self):
        with pytest.raises(ValueError):
            RiskScorer.compute_risk_score(-0.1)

        with pytest.raises(ValueError):
            RiskScorer.compute_risk_score(1.01)

        with pytest.raises(ValueError):
            RiskScorer.compute_risk_score(None)

        with pytest.raises(ValueError):
            RiskScorer.compute_risk_score(np.nan)

    def test_batch_scoring_vectorization(self):
        probs = np.array([0.05, 0.25, 0.65, 0.95])
        scores, bands = RiskScorer.batch_score(probs)

        assert len(scores) == 4
        assert np.array_equal(scores, np.array([5.0, 25.0, 65.0, 95.0]))
        assert bands == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
