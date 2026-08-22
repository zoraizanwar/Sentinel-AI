"""Report Generation & Local Storage Service."""
import os
import uuid
from typing import List, Optional, Tuple
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import SentinelAIException
from backend.app.core.session_store import session_store
from backend.app.models.report import Report, ReportType
from backend.app.models.organization import Organization
from backend.app.models.client import Client
from backend.app.models.analysis import Analysis
from backend.app.repositories.report_repo import ReportRepository
from backend.app.services.reporting.pdf_report import PDFReportGenerator
from backend.app.services.audit_service import AuditService
from backend.app.schemas.report import ReportResponse
from backend.app.schemas.analysis import AnalysisResult


class ReportService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.report_repo = ReportRepository(db)
        self.audit_service = AuditService(db)

    async def list_reports(self, org_id: str, client_id: Optional[str] = None) -> List[ReportResponse]:
        reports = await self.report_repo.list_by_organization(org_id, client_id)
        return [ReportResponse.model_validate(r) for r in reports]

    async def get_report(self, org_id: str, report_id: str) -> ReportResponse:
        report = await self.report_repo.get_by_id(org_id, report_id)
        if not report:
            raise SentinelAIException("Report not found.", status_code=404, code="REPORT_NOT_FOUND")
        return ReportResponse.model_validate(report)

    async def generate_report(
        self,
        org_id: str,
        report_type: ReportType = ReportType.ANALYSIS,
        client_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        title: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ReportResponse:
        org = await self.db.get(Organization, org_id)
        if not org:
            raise SentinelAIException("Organization not found.", status_code=404, code="ORGANIZATION_NOT_FOUND")

        # 1. Fetch Analysis Result from SessionStore or reconstruct from database
        analysis_result: Optional[AnalysisResult] = None
        target_analysis_id = analysis_id

        if not target_analysis_id:
            # Pick latest analysis for client or organization
            if client_id:
                stmt = select(Analysis).where(
                    Analysis.organization_id == org_id,
                    Analysis.client_id == client_id
                ).order_by(Analysis.created_at.desc()).limit(1)
            else:
                stmt = select(Analysis).where(Analysis.organization_id == org_id).order_by(Analysis.created_at.desc()).limit(1)
            
            res = await self.db.execute(stmt)
            latest_analysis = res.scalar_one_or_none()
            if not latest_analysis:
                raise SentinelAIException("No completed analyses available to generate a report.", status_code=400, code="NO_ANALYSIS_AVAILABLE")
            target_analysis_id = latest_analysis.id

        session = session_store.get(target_analysis_id)
        if not session:
            db_analysis = await self.db.get(Analysis, target_analysis_id)
            if not db_analysis or db_analysis.organization_id != org_id:
                raise SentinelAIException("Analysis not found in this organization.", status_code=404, code="ANALYSIS_NOT_FOUND")

            # Try to fetch from persistent analysis service or create session wrapper
            from backend.app.services.persistent_analysis_service import PersistentAnalysisService
            p_service = PersistentAnalysisService(self.db)
            p_analysis = await p_service.get_analysis(org_id, target_analysis_id)
            session = session_store.get(target_analysis_id)

        # 2. Compile PDF via ReportLab engine
        pdf_bytes = PDFReportGenerator.generate_report(session)

        # 3. Save PDF into safe local reports directory
        client_dir = client_id or "general"
        dest_dir = os.path.join(settings.REPORTS_BASE_DIR, "organizations", org_id, "clients", client_dir)
        os.makedirs(dest_dir, exist_ok=True)
        report_file_id = str(uuid.uuid4())[:8]
        report_filename = f"report_{report_type.value.lower()}_{report_file_id}.pdf"
        file_path = os.path.join(dest_dir, report_filename)

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        report_title = title or f"{org.name} — {report_type.value.capitalize()} Fraud Intelligence Report"

        # 4. Record Report in Database
        report = await self.report_repo.create(
            org_id=org_id,
            client_id=client_id,
            analysis_id=target_analysis_id,
            report_type=report_type,
            title=report_title,
            file_path=file_path,
            file_size_bytes=len(pdf_bytes),
            generated_by=user_id
        )

        # 5. Audit Log
        await self.audit_service.log_event(
            org_id=org_id,
            action="REPORT_GENERATED",
            resource_type="REPORT",
            resource_id=report.id,
            user_id=user_id,
            details={"title": report.title, "type": report_type.value, "file_size_bytes": len(pdf_bytes)}
        )
        await self.db.commit()

        return ReportResponse.model_validate(report)

    async def get_download_file(self, org_id: str, report_id: str, user_id: Optional[str] = None) -> Tuple[str, str]:
        report = await self.report_repo.get_by_id(org_id, report_id)
        if not report:
            raise SentinelAIException("Report not found.", status_code=404, code="REPORT_NOT_FOUND")

        if not os.path.exists(report.file_path):
            raise SentinelAIException("Report physical file is missing from local storage.", status_code=404, code="REPORT_FILE_MISSING")

        await self.audit_service.log_event(
            org_id=org_id,
            action="REPORT_DOWNLOADED",
            resource_type="REPORT",
            resource_id=report.id,
            user_id=user_id,
            details={"title": report.title}
        )
        await self.db.commit()

        filename = os.path.basename(report.file_path)
        return report.file_path, filename
