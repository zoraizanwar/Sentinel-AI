"""Transaction Explorer API Router for Sentinel AI."""
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import require_org_member, get_current_user
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.user import User
from backend.app.models.transaction import Transaction
from backend.app.repositories.transaction_repo import TransactionRepository
from backend.app.schemas.transactions import PaginatedTransactionsResponse, TransactionItem
from backend.app.core.session_store import session_store

router = APIRouter()


# 1. Organization & Database-Backed Transaction Explorer Endpoint (Phase 9 Primary)
@router.get(
    "/organizations/{org_id}/analyses/{analysis_id}/transactions",
    response_model=PaginatedTransactionsResponse,
    summary="Explore & Filter Persisted Transactions",
    description="Database-side paginated, sorted, and filtered transaction query under strict tenant isolation."
)
async def get_persisted_transactions(
    org_id: str,
    analysis_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of records per page"),
    sort_by: str = Query("risk_score", description="Column to sort by: risk_score, amount, timestamp, transaction_num"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction: asc or desc"),
    risk_band: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$", description="Filter by risk band"),
    is_fraud: Optional[int] = Query(None, ge=0, le=1, description="Filter by actual fraud label (0=legit, 1=fraud)"),
    predicted_fraud: Optional[int] = Query(None, ge=0, le=1, description="Filter by model prediction (0=legit, 1=flagged)"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum transaction amount in USD"),
    max_amount: Optional[float] = Query(None, ge=0.0, description="Maximum transaction amount in USD"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum risk score (0-100)"),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum risk score (0-100)"),
    search: Optional[str] = Query(None, description="Search term for transaction ID, merchant, category, city, or state"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
) -> PaginatedTransactionsResponse:
    repo = TransactionRepository(db)
    
    # Map frontend sort_by column to model attribute safely
    sort_field_map = {
        "risk_score": "risk_score",
        "amount": "amount",
        "amt": "amount",
        "timestamp": "timestamp",
        "trans_date_trans_time": "timestamp",
        "transaction_num": "transaction_num",
        "trans_num": "transaction_num",
        "fraud_probability": "fraud_probability"
    }
    target_sort = sort_field_map.get(sort_by, "risk_score")

    fraud_only = (predicted_fraud == 1) if predicted_fraud is not None else None

    tx_list, total_matching = await repo.paginate_transactions(
        org_id=org_id,
        analysis_id=analysis_id,
        page=page,
        page_size=page_size,
        sort_by=target_sort,
        sort_order=sort_order,
        risk_band=risk_band,
        min_amount=min_amount,
        max_amount=max_amount,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        fraud_only=fraud_only,
        search=search
    )

    total_pages = max(1, int(np.ceil(total_matching / page_size))) if total_matching > 0 else 1

    items = [
        TransactionItem(
            transaction_id=t.transaction_num,
            timestamp=t.timestamp,
            amount=float(t.amount),
            category=t.category,
            merchant=t.merchant,
            city=t.city,
            state=t.state,
            fraud_probability=float(t.fraud_probability),
            risk_score=float(t.risk_score),
            risk_band=t.risk_band,
            predicted_fraud=t.is_fraud_pred,
            is_actual_fraud=t.actual_fraud_label
        )
        for t in tx_list
    ]

    return PaginatedTransactionsResponse(
        transactions=items,
        total_matching=total_matching,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        sort_by=sort_by,
        sort_order=sort_order,
        applied_filters={
            "risk_band": risk_band,
            "min_amount": min_amount,
            "max_amount": max_amount,
            "search": search
        }
    )


# 2. Legacy In-Memory Session Explorer (Backward Compatibility)
@router.get(
    "/analysis/{analysis_id}/transactions",
    response_model=PaginatedTransactionsResponse,
    summary="Explore Session Transactions",
    description="Queries and paginates transaction predictions from the active in-memory session."
)
def get_session_transactions(
    analysis_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=500, description="Number of records per page"),
    sort_by: str = Query("risk_score", description="Column to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction: asc or desc"),
    risk_band: Optional[str] = Query(None, pattern="^(LOW|MEDIUM|HIGH|CRITICAL)$", description="Filter by risk band"),
    is_fraud: Optional[int] = Query(None, ge=0, le=1, description="Filter by actual fraud flag"),
    predicted_fraud: Optional[int] = Query(None, ge=0, le=1, description="Filter by model prediction"),
    min_amount: Optional[float] = Query(None, ge=0.0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0.0, description="Maximum amount"),
    min_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Min risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Max risk score"),
    search: Optional[str] = Query(None, description="Search keyword")
) -> PaginatedTransactionsResponse:
    session = session_store.get(analysis_id)
    df = session.predictions_df

    filtered_df = df.copy()
    applied_filters: Dict[str, Any] = {}

    if risk_band:
        filtered_df = filtered_df[filtered_df["risk_band"] == risk_band]
        applied_filters["risk_band"] = risk_band

    if is_fraud is not None and "is_actual_fraud" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["is_actual_fraud"] == is_fraud]
        applied_filters["is_fraud"] = is_fraud

    if predicted_fraud is not None and "predicted_fraud" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["predicted_fraud"] == predicted_fraud]
        applied_filters["predicted_fraud"] = predicted_fraud

    if min_amount is not None and "amt" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["amt"] >= min_amount]
        applied_filters["min_amount"] = min_amount

    if max_amount is not None and "amt" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["amt"] <= max_amount]
        applied_filters["max_amount"] = max_amount

    if min_risk_score is not None:
        filtered_df = filtered_df[filtered_df["risk_score"] >= min_risk_score]
        applied_filters["min_risk_score"] = min_risk_score

    if max_risk_score is not None:
        filtered_df = filtered_df[filtered_df["risk_score"] <= max_risk_score]
        applied_filters["max_risk_score"] = max_risk_score

    if search:
        s_term = search.strip().lower()
        search_cols = [c for c in ["trans_num", "merchant", "category", "city", "state"] if c in filtered_df.columns]
        if search_cols:
            match_mask = pd.Series(False, index=filtered_df.index)
            for c in search_cols:
                match_mask |= filtered_df[c].astype(str).str.lower().str.contains(s_term, na=False, regex=False)
            filtered_df = filtered_df[match_mask]
            applied_filters["search"] = search

    total_matching = len(filtered_df)

    valid_sort_cols = {
        "risk_score": "risk_score",
        "fraud_probability": "fraud_probability",
        "amt": "amt",
        "trans_date_trans_time": "trans_date_trans_time",
        "trans_num": "trans_num"
    }
    target_sort = valid_sort_cols.get(sort_by, "risk_score")
    if target_sort in filtered_df.columns:
        ascending = (sort_order.lower() == "asc")
        filtered_df = filtered_df.sort_values(by=target_sort, ascending=ascending)

    total_pages = max(1, int(np.ceil(total_matching / page_size))) if total_matching > 0 else 1
    start_idx = (page - 1) * page_size
    page_df = filtered_df.iloc[start_idx : start_idx + page_size]

    items = []
    for _, row in page_df.iterrows():
        items.append(
            TransactionItem(
                transaction_id=str(row.get("trans_num", "")),
                timestamp=str(row.get("trans_date_trans_time", "")),
                merchant=str(row.get("merchant", "")),
                category=str(row.get("category", "")),
                amount=float(row.get("amt", 0.0)),
                city=str(row.get("city", "")),
                state=str(row.get("state", "")),
                is_actual_fraud=int(row["is_actual_fraud"]) if "is_actual_fraud" in row and pd.notna(row["is_actual_fraud"]) else None,
                predicted_fraud=int(row.get("predicted_fraud", 0)),
                fraud_probability=float(row.get("fraud_probability", 0.0)),
                risk_score=float(row.get("risk_score", 0.0)),
                risk_band=str(row.get("risk_band", "LOW"))
            )
        )

    return PaginatedTransactionsResponse(
        transactions=items,
        total_matching=total_matching,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        sort_by=sort_by,
        sort_order=sort_order,
        applied_filters=applied_filters
    )
