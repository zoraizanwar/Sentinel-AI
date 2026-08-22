"""Machine Learning and Model Evaluation Schemas for Sentinel AI."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ConfusionMatrix(BaseModel):
    true_positive: int = Field(..., description="Correctly identified fraud cases")
    false_positive: int = Field(..., description="Legitimate transactions falsely flagged as fraud")
    true_negative: int = Field(..., description="Correctly identified legitimate cases")
    false_negative: int = Field(..., description="Fraud cases missed by the model")


class CurvePoint(BaseModel):
    x: float = Field(..., description="X-axis value (e.g. Recall or False Positive Rate)")
    y: float = Field(..., description="Y-axis value (e.g. Precision or True Positive Rate)")
    threshold: Optional[float] = Field(None, description="Corresponding classification threshold")


class CandidateModelMetrics(BaseModel):
    model_name: str
    precision: float
    recall: float
    f1: float
    pr_auc: float
    roc_auc: float
    false_positive_rate: float
    false_negative_rate: float
    accuracy: float
    confusion_matrix: ConfusionMatrix
    pr_curve: List[CurvePoint] = Field(default_factory=list)
    roc_curve: List[CurvePoint] = Field(default_factory=list)


class ThresholdOptimizationResult(BaseModel):
    optimal_threshold: float
    methodology: str
    validation_precision: float
    validation_recall: float
    validation_f1: float
    selection_objective: str


class SelectedModelDetails(BaseModel):
    model_name: str
    justification: str
    selection_metric: str
    selection_value: float
    optimal_threshold: float
    threshold_methodology: str


class FeatureImportanceItem(BaseModel):
    feature_name: str
    importance: float
    rank: int


class ModelEvaluationSummary(BaseModel):
    candidate_models: List[CandidateModelMetrics]
    selected_model: SelectedModelDetails
    global_feature_importance: List[FeatureImportanceItem]
    is_xgboost_available: bool = False
    validation_fraud_count: int
    validation_legit_count: int
    test_fraud_count: Optional[int] = None
    test_legit_count: Optional[int] = None
    test_metrics: Optional[CandidateModelMetrics] = None
