"""Dataset Pydantic Schemas."""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.app.models.dataset import DatasetValidationStatus, DatasetProcessingStatus


class DatasetResponse(BaseModel):
    id: str
    organization_id: str
    client_id: str
    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    target_column: Optional[str] = None
    validation_status: DatasetValidationStatus
    validation_summary: Optional[Dict[str, Any]] = None
    processing_status: DatasetProcessingStatus
    uploaded_by: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DatasetListResponse(BaseModel):
    datasets: List[DatasetResponse]
    total_count: int
