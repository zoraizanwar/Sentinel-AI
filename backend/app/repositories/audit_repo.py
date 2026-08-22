"""Audit Log Repository for Append-Only Security Logging."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_event(
        self,
        org_id: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        log = AuditLog(
            organization_id=org_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_by_organization(
        self,
        org_id: str,
        page: int = 1,
        page_size: int = 25,
        action: Optional[str] = None
    ) -> Tuple[List[AuditLog], int]:
        filters = [AuditLog.organization_id == org_id]
        if action:
            filters.append(AuditLog.action == action)

        count_stmt = select(func.count(AuditLog.id)).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        query_stmt = (
            select(AuditLog)
            .options(joinedload(AuditLog.user))
            .where(*filters)
            .order_by(desc(AuditLog.created_at))
            .limit(page_size)
            .offset((page - 1) * page_size)
        )
        result = await self.db.execute(query_stmt)
        return list(result.scalars().all()), total
