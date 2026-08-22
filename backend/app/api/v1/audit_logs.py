"""Audit Logs API Router."""
import math
from typing import Optional, Tuple
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import require_org_admin
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.repositories.audit_repo import AuditLogRepository
from backend.app.schemas.audit_log import PaginatedAuditLogsResponse, AuditLogResponse

router = APIRouter(prefix="/organizations/{org_id}/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=PaginatedAuditLogsResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    action: Optional[str] = Query(None, description="Filter by action code"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_admin),
    db: AsyncSession = Depends(get_db)
):
    """Lists audit logs for the organization with pagination and action filtering (ADMIN required)."""
    org, _ = org_tuple
    repo = AuditLogRepository(db)
    logs, total = await repo.list_by_organization(
        org_id=org.id,
        page=page,
        page_size=page_size,
        action=action
    )

    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    items = [
        AuditLogResponse(
            id=log.id,
            organization_id=log.organization_id,
            user_id=log.user_id,
            user_email=log.user.email if log.user else None,
            user_name=log.user.full_name if log.user else None,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            created_at=log.created_at
        )
        for log in logs
    ]

    return PaginatedAuditLogsResponse(
        items=items,
        total_count=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
