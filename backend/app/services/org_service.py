"""Organization Management & Dashboard Aggregation Service."""
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import SentinelAIException
from backend.app.models.organization import Organization, OrganizationMember, OrganizationRole
from backend.app.models.user import User
from backend.app.models.client import Client
from backend.app.models.dataset import Dataset
from backend.app.models.analysis import Analysis
from backend.app.models.transaction import Transaction
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.repositories.user_repo import UserRepository
from backend.app.services.audit_service import AuditService
from backend.app.schemas.organization import (
    OrganizationResponse,
    OrganizationMemberResponse,
    OrgDashboardResponse,
    HighRiskClientSummary,
    RecentAnalysisSummary
)


class OrganizationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.org_repo = OrganizationRepository(db)
        self.user_repo = UserRepository(db)
        self.audit_service = AuditService(db)

    async def list_user_organizations(self, user_id: str) -> List[OrganizationResponse]:
        org_tuples = await self.org_repo.get_user_organizations(user_id)
        return [
            OrganizationResponse(
                id=org.id,
                name=org.name,
                slug=org.slug,
                description=org.description,
                created_at=org.created_at,
                role=role
            )
            for org, role in org_tuples
        ]

    async def create_organization(
        self,
        user_id: str,
        name: str,
        description: Optional[str] = None
    ) -> OrganizationResponse:
        org = await self.org_repo.create(name=name, description=description)
        member = await self.org_repo.add_member(
            org_id=org.id,
            user_id=user_id,
            role=OrganizationRole.ORGANIZATION_ADMIN
        )
        await self.audit_service.log_event(
            org_id=org.id,
            action="ORGANIZATION_CREATED",
            resource_type="ORGANIZATION",
            resource_id=org.id,
            user_id=user_id,
            details={"name": org.name}
        )
        await self.db.commit()

        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            created_at=org.created_at,
            role=OrganizationRole.ORGANIZATION_ADMIN
        )

    async def get_organization(self, org_id: str, current_user_id: str) -> OrganizationResponse:
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise SentinelAIException("Organization not found.", status_code=404, code="ORGANIZATION_NOT_FOUND")

        member = await self.org_repo.get_member(org_id, current_user_id)
        role = member.role if member else None

        return OrganizationResponse(
            id=org.id,
            name=org.name,
            slug=org.slug,
            description=org.description,
            created_at=org.created_at,
            role=role
        )

    async def list_members(self, org_id: str) -> List[OrganizationMemberResponse]:
        members = await self.org_repo.get_members_with_users(org_id)
        return [
            OrganizationMemberResponse(
                id=m.id,
                user_id=m.user_id,
                email=m.user.email,
                full_name=m.user.full_name,
                role=m.role,
                created_at=m.created_at
            )
            for m in members
        ]

    async def add_member(
        self,
        org_id: str,
        email: str,
        role: OrganizationRole,
        acting_user_id: str
    ) -> OrganizationMemberResponse:
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise SentinelAIException(f"User with email '{email}' does not exist.", status_code=404, code="USER_NOT_FOUND")

        existing_member = await self.org_repo.get_member(org_id, user.id)
        if existing_member:
            raise SentinelAIException("User is already a member of this organization.", status_code=400, code="MEMBER_ALREADY_EXISTS")

        member = await self.org_repo.add_member(org_id, user.id, role)
        await self.audit_service.log_event(
            org_id=org_id,
            action="MEMBER_ADDED",
            resource_type="ORGANIZATION_MEMBER",
            resource_id=member.id,
            user_id=acting_user_id,
            details={"email": user.email, "role": role.value}
        )
        await self.db.commit()

        return OrganizationMemberResponse(
            id=member.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=member.role,
            created_at=member.created_at
        )

    async def remove_member(self, org_id: str, target_user_id: str, acting_user_id: str) -> None:
        if target_user_id == acting_user_id:
            raise SentinelAIException("You cannot remove yourself from the organization.", status_code=400, code="CANNOT_REMOVE_SELF")

        member = await self.org_repo.get_member(org_id, target_user_id)
        if not member:
            raise SentinelAIException("Member not found in this organization.", status_code=404, code="MEMBER_NOT_FOUND")

        await self.org_repo.remove_member(member)
        await self.audit_service.log_event(
            org_id=org_id,
            action="MEMBER_REMOVED",
            resource_type="ORGANIZATION_MEMBER",
            resource_id=member.id,
            user_id=acting_user_id,
            details={"removed_user_id": target_user_id}
        )
        await self.db.commit()

    async def get_organization_dashboard(self, org_id: str) -> OrgDashboardResponse:
        org = await self.org_repo.get_by_id(org_id)
        if not org:
            raise SentinelAIException("Organization not found.", status_code=404, code="ORGANIZATION_NOT_FOUND")

        # Counts
        clients_count = (await self.db.execute(select(func.count(Client.id)).where(Client.organization_id == org_id))).scalar_one()
        datasets_count = (await self.db.execute(select(func.count(Dataset.id)).where(Dataset.organization_id == org_id))).scalar_one()
        analyses_count = (await self.db.execute(select(func.count(Analysis.id)).where(Analysis.organization_id == org_id))).scalar_one()

        # Aggregate across all completed analyses
        analyses_stmt = select(Analysis).where(Analysis.organization_id == org_id).order_by(Analysis.created_at.desc())
        analyses = list((await self.db.execute(analyses_stmt)).scalars().all())

        total_tx = 0
        total_fraud = 0
        total_exposure = 0.0
        critical_count = 0
        high_count = 0
        category_exposure_map: Dict[str, float] = {}

        for a in analyses:
            f_stats = a.fraud_statistics or {}
            r_stats = a.risk_statistics or {}
            total_tx += f_stats.get("total_transactions", 0)
            total_fraud += f_stats.get("fraud_count", 0)
            total_exposure += f_stats.get("fraud_volume_usd", 0.0)

            bands = r_stats.get("risk_bands", {})
            critical_count += bands.get("CRITICAL", {}).get("count", 0)
            high_count += bands.get("HIGH", {}).get("count", 0)

            for cat in a.category_breakdown or []:
                c_name = cat.get("category", "other")
                c_vol = cat.get("fraud_volume_usd", 0.0)
                category_exposure_map[c_name] = category_exposure_map.get(c_name, 0.0) + c_vol

        overall_fraud_rate = (total_fraud / total_tx * 100.0) if total_tx > 0 else 0.0

        # Recent analyses summaries
        recent_analyses_dto = []
        for a in analyses[:5]:
            client = await self.db.get(Client, a.client_id)
            f_stats = a.fraud_statistics or {}
            recent_analyses_dto.append(
                RecentAnalysisSummary(
                    analysis_id=a.id,
                    client_name=client.name if client else "Unknown Client",
                    model_name=a.model_name,
                    total_transactions=f_stats.get("total_transactions", 0),
                    fraud_count=f_stats.get("fraud_count", 0),
                    fraud_rate_percentage=f_stats.get("fraud_rate_percentage", 0.0),
                    created_at=a.created_at
                )
            )

        # High risk clients summary
        clients_stmt = select(Client).where(Client.organization_id == org_id)
        clients = list((await self.db.execute(clients_stmt)).scalars().all())
        high_risk_clients_dto = []

        for c in clients:
            c_analyses_stmt = select(Analysis).where(Analysis.client_id == c.id)
            c_analyses = list((await self.db.execute(c_analyses_stmt)).scalars().all())
            c_fraud = 0
            c_tx = 0
            c_exposure = 0.0
            c_crit = 0
            c_high = 0

            for ca in c_analyses:
                f_s = ca.fraud_statistics or {}
                r_s = ca.risk_statistics or {}
                c_tx += f_s.get("total_transactions", 0)
                c_fraud += f_s.get("fraud_count", 0)
                c_exposure += f_s.get("fraud_volume_usd", 0.0)
                bands = r_s.get("risk_bands", {})
                c_crit += bands.get("CRITICAL", {}).get("count", 0)
                c_high += bands.get("HIGH", {}).get("count", 0)

            c_rate = (c_fraud / c_tx * 100.0) if c_tx > 0 else 0.0
            high_risk_clients_dto.append(
                HighRiskClientSummary(
                    client_id=c.id,
                    client_code=c.client_code,
                    name=c.name,
                    fraud_count=c_fraud,
                    fraud_rate_percentage=round(c_rate, 4),
                    critical_risk_count=c_crit,
                    high_risk_count=c_high,
                    financial_exposure_usd=round(c_exposure, 2)
                )
            )

        high_risk_clients_dto.sort(key=lambda x: x.financial_exposure_usd, reverse=True)

        cat_list = [
            {"category": k, "fraud_exposure_usd": round(v, 2)}
            for k, v in sorted(category_exposure_map.items(), key=lambda item: item[1], reverse=True)[:10]
        ]

        return OrgDashboardResponse(
            organization_id=org.id,
            organization_name=org.name,
            total_clients=clients_count,
            total_datasets=datasets_count,
            total_analyses=analyses_count,
            total_transactions_analyzed=total_tx,
            total_fraud_transactions=total_fraud,
            overall_fraud_rate_percentage=round(overall_fraud_rate, 4),
            total_financial_exposure_usd=round(total_exposure, 2),
            critical_risk_count=critical_count,
            high_risk_count=high_count,
            highest_risk_clients=high_risk_clients_dto[:5],
            recent_analyses=recent_analyses_dto,
            category_exposure=cat_list
        )
