"""Pydantic schemas for Sentinel AI."""
from .common import HealthResponse, ErrorResponse
from .validation import (
    Severity,
    ValidationFinding,
    ValidationStatus,
    ColumnSummary,
    ClassDistribution,
    DatasetInspectionResult,
    DataQualityReport,
)
from .ml import (
    ConfusionMatrix,
    CurvePoint,
    CandidateModelMetrics,
    ThresholdOptimizationResult,
    SelectedModelDetails,
    FeatureImportanceItem,
    ModelEvaluationSummary,
)
from .explainability import (
    SHAPContribution,
    LocalExplanation,
    GlobalFeatureImportance,
)
from .transactions import (
    TransactionItem,
    PaginatedTransactionsResponse,
)
from .analysis import (
    FraudStatistics,
    RiskStatistics,
    RiskDistributionSummary,
    CategoricalBreakdown,
    RiskPattern,
    AnalyticalFinding,
    EvidenceBasedRecommendation,
    TransactionPaginationMeta,
    AnalysisResult,
)

__all__ = [
    "HealthResponse",
    "ErrorResponse",
    "Severity",
    "ValidationFinding",
    "ValidationStatus",
    "ColumnSummary",
    "ClassDistribution",
    "DatasetInspectionResult",
    "DataQualityReport",
    "ConfusionMatrix",
    "CurvePoint",
    "CandidateModelMetrics",
    "ThresholdOptimizationResult",
    "SelectedModelDetails",
    "FeatureImportanceItem",
    "ModelEvaluationSummary",
    "SHAPContribution",
    "LocalExplanation",
    "GlobalFeatureImportance",
    "TransactionItem",
    "PaginatedTransactionsResponse",
    "FraudStatistics",
    "RiskStatistics",
    "RiskDistributionSummary",
    "CategoricalBreakdown",
    "RiskPattern",
    "AnalyticalFinding",
    "EvidenceBasedRecommendation",
    "TransactionPaginationMeta",
    "AnalysisResult",
]
