"""PDF Audit Reporting API Router for Sentinel AI."""
import os
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_analyst
)
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.report import ReportType
from backend.app.services.report_service import ReportService
from backend.app.schemas.report import ReportGenerateRequest, ReportResponse, ReportListResponse
from backend.app.services.reporting.pdf_report import PDFReportGenerator
from backend.app.core.session_store import session_store

router = APIRouter()


# 1. Organization-Scoped Report Generation (Phase 9 Primary)
@router.post(
    "/organizations/{org_id}/reports/generate",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Multi-Scope PDF Audit Report",
    description="Compiles an executive PDF report (Organization, Client, or Analysis scope) and records metadata in PostgreSQL."
)
async def generate_org_report(
    org_id: str,
    payload: ReportGenerateRequest,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_analyst),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    return await service.generate_report(
        org_id=org_id,
        report_type=payload.report_type,
        client_id=payload.client_id,
        analysis_id=payload.analysis_id,
        title=payload.title,
        user_id=current_user.id
    )


@router.get(
    "/organizations/{org_id}/reports",
    response_model=List[ReportResponse],
    summary="List Generated Reports",
    description="Lists all persisted PDF audit reports for the organization or a specific client."
)
async def list_org_reports(
    org_id: str,
    client_id: Optional[str] = Query(None, description="Optional client ID filter"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    return await service.list_reports(org_id=org_id, client_id=client_id)


@router.get(
    "/organizations/{org_id}/reports/{report_id}/download",
    summary="Download Generated PDF Report",
    description="Downloads the binary PDF file stream for an authorized organization report."
)
async def download_org_report(
    org_id: str,
    report_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    service = ReportService(db)
    file_path, filename = await service.get_download_file(
        org_id=org_id,
        report_id=report_id,
        user_id=current_user.id
    )
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )


# 2. Legacy In-Memory Session Report Route (Backward Compatibility)
@router.post(
    "/analysis/{analysis_id}/report/pdf",
    summary="Generate PDF Audit Report (Session)",
    description="Compiles and streams a multi-page PDF audit report directly from an active in-memory analysis session."
)
def generate_session_pdf_report(analysis_id: str):
    session = session_store.get(analysis_id)
    pdf_bytes = PDFReportGenerator.generate_report(session)

    filename = f"sentinel_ai_fraud_intelligence_report_{analysis_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )
