"""Report Pydantic Schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.app.models.report import ReportType


class ReportGenerateRequest(BaseModel):
    report_type: ReportType = ReportType.ANALYSIS
    client_id: Optional[str] = None
    analysis_id: Optional[str] = None
    title: Optional[str] = None


class ReportResponse(BaseModel):
    id: str
    organization_id: str
    client_id: Optional[str] = None
    analysis_id: Optional[str] = None
    report_type: ReportType
    title: str
    file_size_bytes: int
    generated_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: List[ReportResponse]
    total_count: int
