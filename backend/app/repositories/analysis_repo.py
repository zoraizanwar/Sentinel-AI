"""Analysis Repository for Persistent Fraud Evaluation Runs."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analysis import Analysis, AnalysisStatus
from backend.app.models.client import Client
from backend.app.models.dataset import Dataset


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: str, analysis_id: str) -> Optional[Analysis]:
        stmt = (
            select(Analysis)
            .options(
                joinedload(Analysis.client),
                joinedload(Analysis.dataset)
            )
            .where(
                Analysis.id == analysis_id,
                Analysis.organization_id == org_id
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_organization(
        self,
        org_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Analysis]:
        stmt = (
            select(Analysis)
            .options(
                joinedload(Analysis.client),
                joinedload(Analysis.dataset)
            )
            .where(Analysis.organization_id == org_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_client(
        self,
        org_id: str,
        client_id: str,
        limit: int = 50
    ) -> List[Analysis]:
        stmt = (
            select(Analysis)
            .options(joinedload(Analysis.dataset))
            .where(
                Analysis.organization_id == org_id,
                Analysis.client_id == client_id
            )
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        org_id: str,
        client_id: str,
        dataset_id: str,
        user_id: Optional[str],
        model_name: str,
        optimal_threshold: float,
        execution_time_seconds: float,
        validation_metrics: dict,
        test_metrics: Optional[dict],
        fraud_statistics: dict,
        risk_statistics: dict,
        category_breakdown: list,
        empirical_findings: list,
        recommendations: list,
        global_feature_importance: list,
        status: AnalysisStatus = AnalysisStatus.COMPLETED
    ) -> Analysis:
        analysis = Analysis(
            organization_id=org_id,
            client_id=client_id,
            dataset_id=dataset_id,
            user_id=user_id,
            model_name=model_name,
            optimal_threshold=optimal_threshold,
            execution_time_seconds=execution_time_seconds,
            validation_metrics=validation_metrics,
            test_metrics=test_metrics,
            fraud_statistics=fraud_statistics,
            risk_statistics=risk_statistics,
            category_breakdown=category_breakdown,
            empirical_findings=empirical_findings,
            recommendations=recommendations,
            global_feature_importance=global_feature_importance,
            status=status
        )
        self.db.add(analysis)
        await self.db.flush()
        return analysis
