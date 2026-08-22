"""Client Management & Client Risk Dashboard Service."""
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import SentinelAIException
from backend.app.models.client import Client, ClientStatus
from backend.app.models.dataset import Dataset
from backend.app.models.analysis import Analysis
from backend.app.models.transaction import Transaction
from backend.app.repositories.client_repo import ClientRepository
from backend.app.services.audit_service import AuditService
from backend.app.schemas.client import ClientResponse, ClientDashboardResponse


class ClientService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.client_repo = ClientRepository(db)
        self.audit_service = AuditService(db)

    async def list_clients(
        self,
        org_id: str,
        status: Optional[ClientStatus] = None,
        search: Optional[str] = None
    ) -> List[ClientResponse]:
        clients = await self.client_repo.list_clients(org_id=org_id, status=status, search=search)
        client_responses = []

        for c in clients:
            analyses_count = (await self.db.execute(select(func.count(Analysis.id)).where(Analysis.client_id == c.id))).scalar_one()
            datasets_count = (await self.db.execute(select(func.count(Dataset.id)).where(Dataset.client_id == c.id))).scalar_one()

            # Aggregate total transactions & frauds
            analyses = list((await self.db.execute(select(Analysis).where(Analysis.client_id == c.id))).scalars().all())
            tot_tx = sum((a.fraud_statistics or {}).get("total_transactions", 0) for a in analyses)
            tot_fraud = sum((a.fraud_statistics or {}).get("fraud_count", 0) for a in analyses)

            client_responses.append(
                ClientResponse(
                    id=c.id,
                    organization_id=c.organization_id,
                    client_code=c.client_code,
                    name=c.name,
                    email=c.email,
                    industry=c.industry,
                    status=c.status,
                    created_at=c.created_at,
                    updated_at=c.updated_at,
                    total_analyses=analyses_count,
                    total_datasets=datasets_count,
                    total_transactions=tot_tx,
                    fraud_transactions=tot_fraud
                )
            )
        return client_responses

    async def create_client(
        self,
        org_id: str,
        client_code: str,
        name: str,
        email: Optional[str] = None,
        industry: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ClientResponse:
        existing = await self.client_repo.get_by_code(org_id, client_code)
        if existing:
            raise SentinelAIException(f"Client code '{client_code}' already exists in this organization.", status_code=400, code="CLIENT_CODE_EXISTS")

        client = await self.client_repo.create(
            org_id=org_id,
            client_code=client_code,
            name=name,
            email=email,
            industry=industry
        )

        await self.audit_service.log_event(
            org_id=org_id,
            action="CLIENT_CREATED",
            resource_type="CLIENT",
            resource_id=client.id,
            user_id=user_id,
            details={"client_code": client.client_code, "name": client.name}
        )
        await self.db.commit()

        return ClientResponse(
            id=client.id,
            organization_id=client.organization_id,
            client_code=client.client_code,
            name=client.name,
            email=client.email,
            industry=client.industry,
            status=client.status,
            created_at=client.created_at,
            updated_at=client.updated_at
        )

    async def update_client(
        self,
        org_id: str,
        client_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[ClientStatus] = None,
        user_id: Optional[str] = None
    ) -> ClientResponse:
        client = await self.client_repo.get_by_id(org_id, client_id)
        if not client:
            raise SentinelAIException("Client not found.", status_code=404, code="CLIENT_NOT_FOUND")

        updated = await self.client_repo.update(
            client=client,
            name=name,
            email=email,
            industry=industry,
            status=status
        )

        await self.audit_service.log_event(
            org_id=org_id,
            action="CLIENT_UPDATED",
            resource_type="CLIENT",
            resource_id=client.id,
            user_id=user_id,
            details={"status": client.status.value if status else None}
        )
        await self.db.commit()

        return ClientResponse(
            id=updated.id,
            organization_id=updated.organization_id,
            client_code=updated.client_code,
            name=updated.name,
            email=updated.email,
            industry=updated.industry,
            status=updated.status,
            created_at=updated.created_at,
            updated_at=updated.updated_at
        )

    async def get_client_dashboard(self, org_id: str, client_id: str) -> ClientDashboardResponse:
        client = await self.client_repo.get_by_id(org_id, client_id)
        if not client:
            raise SentinelAIException("Client not found.", status_code=404, code="CLIENT_NOT_FOUND")

        analyses_stmt = select(Analysis).where(
            Analysis.organization_id == org_id,
            Analysis.client_id == client_id
        ).order_by(desc(Analysis.created_at))
        analyses = list((await self.db.execute(analyses_stmt)).scalars().all())

        tot_tx = 0
        tot_fraud = 0
        tot_exposure = 0.0
        crit_count = 0
        high_count = 0
        med_count = 0
        low_count = 0
        weighted_score_sum = 0.0
        category_map: Dict[str, float] = {}
        all_risk_factors: List[Dict[str, Any]] = []

        for a in analyses:
            f_s = a.fraud_statistics or {}
            r_s = a.risk_statistics or {}
            tx_count = f_s.get("total_transactions", 0)
            tot_tx += tx_count
            tot_fraud += f_s.get("fraud_count", 0)
            tot_exposure += f_s.get("fraud_volume_usd", 0.0)

            bands = r_s.get("risk_bands", {})
            crit_count += bands.get("CRITICAL", {}).get("count", 0)
            high_count += bands.get("HIGH", {}).get("count", 0)
            med_count += bands.get("MEDIUM", {}).get("count", 0)
            low_count += bands.get("LOW", {}).get("count", 0)

            avg_score = r_s.get("average_risk_score", 0.0)
            weighted_score_sum += (avg_score * tx_count)

            for cat in a.category_breakdown or []:
                c_name = cat.get("category", "other")
                category_map[c_name] = category_map.get(c_name, 0.0) + cat.get("fraud_volume_usd", 0.0)

            if a.global_feature_importance and not all_risk_factors:
                all_risk_factors = a.global_feature_importance[:5]

        fraud_rate = (tot_fraud / tot_tx * 100.0) if tot_tx > 0 else 0.0
        overall_avg_score = (weighted_score_sum / tot_tx) if tot_tx > 0 else 0.0

        risk_dist = {
            "LOW": round((low_count / tot_tx * 100.0), 2) if tot_tx > 0 else 0.0,
            "MEDIUM": round((med_count / tot_tx * 100.0), 2) if tot_tx > 0 else 0.0,
            "HIGH": round((high_count / tot_tx * 100.0), 2) if tot_tx > 0 else 0.0,
            "CRITICAL": round((crit_count / tot_tx * 100.0), 2) if tot_tx > 0 else 0.0,
        }

        # Fetch recent high-risk / suspicious transactions for this client
        tx_stmt = select(Transaction).where(
            Transaction.organization_id == org_id,
            Transaction.client_id == client_id,
            Transaction.risk_score >= 50.0
        ).order_by(desc(Transaction.risk_score), desc(Transaction.created_at)).limit(10)
        recent_txs = list((await self.db.execute(tx_stmt)).scalars().all())

        recent_tx_dicts = [
            {
                "id": t.id,
                "transaction_num": t.transaction_num,
                "timestamp": t.timestamp,
                "merchant": t.merchant,
                "category": t.category,
                "amount": t.amount,
                "risk_score": t.risk_score,
                "risk_band": t.risk_band,
                "is_fraud_pred": t.is_fraud_pred
            }
            for t in recent_txs
        ]

        recent_analyses_dicts = [
            {
                "id": a.id,
                "model_name": a.model_name,
                "optimal_threshold": a.optimal_threshold,
                "total_transactions": (a.fraud_statistics or {}).get("total_transactions", 0),
                "fraud_count": (a.fraud_statistics or {}).get("fraud_count", 0),
                "fraud_rate_percentage": (a.fraud_statistics or {}).get("fraud_rate_percentage", 0.0),
                "created_at": a.created_at
            }
            for a in analyses[:5]
        ]

        cat_list = [
            {"category": k, "fraud_exposure_usd": round(v, 2)}
            for k, v in sorted(category_map.items(), key=lambda item: item[1], reverse=True)[:8]
        ]

        client_dto = ClientResponse(
            id=client.id,
            organization_id=client.organization_id,
            client_code=client.client_code,
            name=client.name,
            email=client.email,
            industry=client.industry,
            status=client.status,
            created_at=client.created_at,
            updated_at=client.updated_at,
            total_analyses=len(analyses),
            total_datasets=len(analyses),
            total_transactions=tot_tx,
            fraud_transactions=tot_fraud
        )

        return ClientDashboardResponse(
            client=client_dto,
            total_transactions=tot_tx,
            fraud_transactions=tot_fraud,
            fraud_rate_percentage=round(fraud_rate, 4),
            total_financial_exposure_usd=round(tot_exposure, 2),
            critical_risk_count=crit_count,
            high_risk_count=high_count,
            medium_risk_count=med_count,
            low_risk_count=low_count,
            average_risk_score=round(overall_avg_score, 2),
            risk_distribution_percentage=risk_dist,
            category_exposure=cat_list,
            top_risk_factors=all_risk_factors,
            recent_suspicious_transactions=recent_tx_dicts,
            recent_analyses=recent_analyses_dicts
        )
