"""Single Source of Truth Analysis Result Schema for Sentinel AI."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from .validation import DatasetInspectionResult, DataQualityReport
from .ml import ModelEvaluationSummary, SelectedModelDetails, FeatureImportanceItem


class FraudStatistics(BaseModel):
    total_transactions: int
    fraud_count: int
    legitimate_count: int
    fraud_rate_percentage: float
    total_volume_usd: float
    fraud_volume_usd: float
    fraud_loss_percentage: float


class RiskStatistics(BaseModel):
    low_risk_count: int
    low_risk_pct: float
    medium_risk_count: int
    medium_risk_pct: float
    high_risk_count: int
    high_risk_pct: float
    critical_risk_count: int
    critical_risk_pct: float
    mean_risk_score: float
    median_risk_score: float


class RiskDistributionSummary(BaseModel):
    score_bins: List[str]
    counts: List[int]
    fraud_counts_per_bin: List[int]


class CategoricalBreakdown(BaseModel):
    category_name: str
    total_count: int
    fraud_count: int
    fraud_rate_percentage: float
    total_volume_usd: float
    fraud_volume_usd: float


class RiskPattern(BaseModel):
    pattern_name: str
    description: str
    affected_count: int
    fraud_rate_percentage: float
    severity: str


class AnalyticalFinding(BaseModel):
    finding_id: str
    title: str
    description: str
    category: str
    evidence_metric: str
    evidence_value: Any


class EvidenceBasedRecommendation(BaseModel):
    recommendation_id: str
    title: str
    action: str
    rationale: str
    priority: str
    expected_impact: str


class TransactionRecord(BaseModel):
    transaction_id: str
    timestamp: str
    amount: float
    category: str
    fraud_probability: float
    risk_score: float
    risk_band: str
    is_actual_fraud: Optional[int] = None
    predicted_fraud: int
    top_risk_factor: Optional[str] = None


class TransactionPaginationMeta(BaseModel):
    total_records: int
    page: int
    page_size: int
    total_pages: int


class AnalysisResult(BaseModel):
    analysis_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_seconds: float
    dataset_summary: DatasetInspectionResult
    data_quality: DataQualityReport
    fraud_statistics: FraudStatistics
    risk_statistics: RiskStatistics
    model_results: ModelEvaluationSummary
    risk_distribution: RiskDistributionSummary
    categorical_breakdowns: Dict[str, CategoricalBreakdown] = Field(default_factory=dict)
    high_risk_patterns: List[RiskPattern] = Field(default_factory=list)
    findings: List[AnalyticalFinding] = Field(default_factory=list)
    recommendations: List[EvidenceBasedRecommendation] = Field(default_factory=list)
    pagination_meta: TransactionPaginationMeta
