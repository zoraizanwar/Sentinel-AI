"""Explainability and SHAP Schemas for Sentinel AI."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SHAPContribution(BaseModel):
    feature_name: str
    feature_value: Any
    shap_value: float
    contribution_type: str = Field(..., description="'RISK_INCREASING' or 'RISK_DECREASING'")
    human_explanation: str


class LocalExplanation(BaseModel):
    transaction_id: str
    fraud_probability: float
    risk_score: float
    risk_band: str
    base_value: float
    positive_contributions: List[SHAPContribution] = Field(
        default_factory=list, description="Top factors increasing fraud risk"
    )
    negative_contributions: List[SHAPContribution] = Field(
        default_factory=list, description="Top factors decreasing fraud risk / supporting legitimacy"
    )
    method: str
    is_cached: bool = False


class GlobalFeatureImportance(BaseModel):
    method: str
    features: List[Dict[str, Any]]
