"""Transaction Repository for Database-Side Paginated, Filtered and Sorted Queries."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc, asc, insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.transaction import Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_tx_num(
        self,
        org_id: str,
        analysis_id: str,
        transaction_num: str
    ) -> Optional[Transaction]:
        stmt = select(Transaction).where(
            Transaction.organization_id == org_id,
            Transaction.analysis_id == analysis_id,
            Transaction.transaction_num == transaction_num
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def paginate_transactions(
        self,
        org_id: str,
        analysis_id: str,
        page: int = 1,
        page_size: int = 25,
        sort_by: str = "risk_score",
        sort_order: str = "desc",
        risk_band: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        fraud_only: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Transaction], int]:
        # Base filter conditions
        filters = [
            Transaction.organization_id == org_id,
            Transaction.analysis_id == analysis_id
        ]

        if risk_band:
            filters.append(Transaction.risk_band == risk_band.upper())

        if min_amount is not None:
            filters.append(Transaction.amount >= min_amount)

        if max_amount is not None:
            filters.append(Transaction.amount <= max_amount)

        if min_risk_score is not None:
            filters.append(Transaction.risk_score >= min_risk_score)

        if max_risk_score is not None:
            filters.append(Transaction.risk_score <= max_risk_score)

        if fraud_only is True:
            filters.append(Transaction.is_fraud_pred == 1)

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            filters.append(
                func.lower(Transaction.transaction_num).like(search_pattern) |
                func.lower(Transaction.merchant).like(search_pattern) |
                func.lower(Transaction.category).like(search_pattern) |
                func.lower(Transaction.city).like(search_pattern) |
                func.lower(Transaction.state).like(search_pattern)
            )

        # 1. Total matching count query
        count_stmt = select(func.count(Transaction.id)).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total_count = count_res.scalar_one()

        # 2. Sorting & Pagination query
        query_stmt = select(Transaction).where(*filters)

        # Map sort columns safely to prevent SQL injection
        sort_column = getattr(Transaction, sort_by, Transaction.risk_score)
        if sort_order.lower() == "asc":
            query_stmt = query_stmt.order_by(asc(sort_column))
        else:
            query_stmt = query_stmt.order_by(desc(sort_column))

        offset = (page - 1) * page_size
        query_stmt = query_stmt.limit(page_size).offset(offset)

        result = await self.db.execute(query_stmt)
        transactions = list(result.scalars().all())

        return transactions, total_count

    async def bulk_insert(self, tx_records: List[Dict[str, Any]], batch_size: int = 5000) -> None:
        """Executes batched bulk insert of transaction dictionaries."""
        for i in range(0, len(tx_records), batch_size):
            chunk = tx_records[i : i + batch_size]
            await self.db.execute(insert(Transaction), chunk)
        await self.db.flush()
