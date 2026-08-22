"""Report Repository for Multi-Scope PDF Audit Reports."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.report import Report, ReportType


class ReportRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: str, report_id: str) -> Optional[Report]:
        stmt = select(Report).where(
            Report.id == report_id,
            Report.organization_id == org_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        org_id: str,
        client_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Report]:
        stmt = select(Report).where(Report.organization_id == org_id)
        if client_id:
            stmt = stmt.where(Report.client_id == client_id)
        stmt = stmt.order_by(Report.created_at.desc()).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        org_id: str,
        title: str,
        file_path: str,
        file_size_bytes: int,
        report_type: ReportType = ReportType.ANALYSIS,
        client_id: Optional[str] = None,
        analysis_id: Optional[str] = None,
        generated_by: Optional[str] = None
    ) -> Report:
        report = Report(
            organization_id=org_id,
            client_id=client_id,
            analysis_id=analysis_id,
            report_type=report_type,
            title=title,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            generated_by=generated_by
        )
        self.db.add(report)
        await self.db.flush()
        return report
