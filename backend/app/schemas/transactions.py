"""Transaction Explorer Schemas for Sentinel AI."""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class TransactionItem(BaseModel):
    transaction_id: str
    timestamp: Optional[str] = None
    amount: float
    category: Optional[str] = None
    merchant: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    fraud_probability: float
    risk_score: float
    risk_band: str
    predicted_fraud: int
    is_actual_fraud: Optional[int] = None


class PaginatedTransactionsResponse(BaseModel):
    transactions: List[TransactionItem]
    total_matching: int
    page: int
    page_size: int
    total_pages: int
    sort_by: str
    sort_order: str
    applied_filters: Dict[str, Any] = Field(default_factory=dict)
