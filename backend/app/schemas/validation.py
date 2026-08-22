"""Validation and Data Quality Schemas for Sentinel AI."""
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    WARNINGS = "WARNINGS"
    INVALID = "INVALID"


class ValidationFinding(BaseModel):
    severity: Severity = Field(..., description="Severity level: ERROR, WARNING, or INFO")
    code: str = Field(..., description="Machine-readable error/warning code")
    message: str = Field(..., description="Human-readable explanation of finding")
    column: Optional[str] = Field(None, description="Associated column name if applicable")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Diagnostic context")


class ColumnSummary(BaseModel):
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    is_numeric: bool
    is_categorical: bool
    is_datetime: bool
    is_constant: bool
    is_high_cardinality: bool
    is_identifier_candidate: bool
    is_leakage_candidate: bool
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    sample_values: List[Any] = Field(default_factory=list)


class ClassDistribution(BaseModel):
    target_column: str
    total_count: int
    legitimate_count: int
    fraud_count: int
    fraud_percentage: float
    imbalance_ratio: float
    is_single_class: bool
    is_severely_imbalanced: bool


class DatasetInspectionResult(BaseModel):
    dataset_name: str
    file_size_bytes: int
    row_count: int
    column_count: int
    target_column: Optional[str] = None
    validation_status: ValidationStatus
    errors: List[ValidationFinding] = Field(default_factory=list)
    warnings: List[ValidationFinding] = Field(default_factory=list)
    infos: List[ValidationFinding] = Field(default_factory=list)
    columns: Dict[str, ColumnSummary] = Field(default_factory=dict)
    class_distribution: Optional[ClassDistribution] = None
    detected_numeric_columns: List[str] = Field(default_factory=list)
    detected_categorical_columns: List[str] = Field(default_factory=list)
    detected_temporal_columns: List[str] = Field(default_factory=list)
    detected_amount_columns: List[str] = Field(default_factory=list)
    detected_id_columns: List[str] = Field(default_factory=list)
    potential_leakage_columns: List[str] = Field(default_factory=list)
    duplicate_rows_count: int = 0
    total_missing_cells: int = 0


class DataQualityReport(BaseModel):
    is_valid_for_analysis: bool
    total_rows: int
    total_columns: int
    missing_cells_percentage: float
    duplicate_rows_percentage: float
    has_target: bool
    target_column_name: Optional[str] = None
    fraud_rate_percentage: Optional[float] = None
    validation_findings_count: Dict[str, int]
    findings: List[ValidationFinding]
