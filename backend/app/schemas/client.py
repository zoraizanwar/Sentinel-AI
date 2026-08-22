"""Client Pydantic Schemas."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.models.client import ClientStatus


class ClientCreate(BaseModel):
    client_code: str = Field(..., min_length=2, max_length=64, description="Unique client code (e.g. ACME-01)")
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    industry: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    industry: Optional[str] = None
    status: Optional[ClientStatus] = None


class ClientResponse(BaseModel):
    id: str
    organization_id: str
    client_code: str
    name: str
    email: Optional[str] = None
    industry: Optional[str] = None
    status: ClientStatus
    created_at: datetime
    updated_at: datetime
    total_analyses: int = 0
    total_datasets: int = 0
    total_transactions: int = 0
    fraud_transactions: int = 0

    model_config = {"from_attributes": True}


class ClientDashboardResponse(BaseModel):
    client: ClientResponse
    total_transactions: int
    fraud_transactions: int
    fraud_rate_percentage: float
    total_financial_exposure_usd: float
    critical_risk_count: int
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    average_risk_score: float
    risk_distribution_percentage: Dict[str, float]
    category_exposure: List[Dict[str, Any]] = []
    top_risk_factors: List[Dict[str, Any]] = []
    recent_suspicious_transactions: List[Dict[str, Any]] = []
    recent_analyses: List[Dict[str, Any]] = []
