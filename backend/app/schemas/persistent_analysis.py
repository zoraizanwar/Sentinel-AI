"""Persistent Analysis Pydantic Schemas."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.app.models.analysis import AnalysisStatus


class AnalysisListItemResponse(BaseModel):
    id: str
    organization_id: str
    client_id: str
    client_name: Optional[str] = None
    client_code: Optional[str] = None
    dataset_id: str
    dataset_filename: Optional[str] = None
    model_name: str
    optimal_threshold: float
    execution_time_seconds: Optional[float] = None
    total_transactions: int
    fraud_transactions: int
    fraud_rate_percentage: float
    financial_exposure_usd: float
    status: AnalysisStatus
    created_at: datetime


class PersistentAnalysisResponse(BaseModel):
    id: str
    organization_id: str
    client_id: str
    client_name: Optional[str] = None
    client_code: Optional[str] = None
    dataset_id: str
    dataset_filename: Optional[str] = None
    user_id: Optional[str] = None
    model_name: str
    optimal_threshold: float
    execution_time_seconds: float
    status: AnalysisStatus
    validation_metrics: Dict[str, Any]
    test_metrics: Optional[Dict[str, Any]] = None
    fraud_statistics: Dict[str, Any]
    risk_statistics: Dict[str, Any]
    category_breakdown: List[Dict[str, Any]]
    empirical_findings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    global_feature_importance: List[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}
