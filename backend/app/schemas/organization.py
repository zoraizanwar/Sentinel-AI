"""Organization Pydantic Schemas."""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from backend.app.models.organization import OrganizationRole


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    role: Optional[OrganizationRole] = None

    model_config = {"from_attributes": True}


class OrganizationMemberResponse(BaseModel):
    id: str
    user_id: str
    email: str
    full_name: str
    role: OrganizationRole
    created_at: datetime


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: OrganizationRole = OrganizationRole.ANALYST


class HighRiskClientSummary(BaseModel):
    client_id: str
    client_code: str
    name: str
    fraud_count: int
    fraud_rate_percentage: float
    critical_risk_count: int
    high_risk_count: int
    financial_exposure_usd: float


class RecentAnalysisSummary(BaseModel):
    analysis_id: str
    client_name: str
    model_name: str
    total_transactions: int
    fraud_count: int
    fraud_rate_percentage: float
    created_at: datetime


class OrgDashboardResponse(BaseModel):
    organization_id: str
    organization_name: str
    total_clients: int
    total_datasets: int
    total_analyses: int
    total_transactions_analyzed: int
    total_fraud_transactions: int
    overall_fraud_rate_percentage: float
    total_financial_exposure_usd: float
    critical_risk_count: int
    high_risk_count: int
    highest_risk_clients: List[HighRiskClientSummary] = []
    recent_analyses: List[RecentAnalysisSummary] = []
    category_exposure: List[Dict[str, Any]] = []
