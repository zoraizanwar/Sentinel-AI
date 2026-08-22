"""Client Repository for Multi-Client Management and Isolation."""
from typing import List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.client import Client, ClientStatus


class ClientRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: str, client_id: str) -> Optional[Client]:
        stmt = select(Client).where(
            Client.id == client_id,
            Client.organization_id == org_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, org_id: str, client_code: str) -> Optional[Client]:
        stmt = select(Client).where(
            Client.organization_id == org_id,
            Client.client_code == client_code.upper().strip()
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_clients(
        self,
        org_id: str,
        status: Optional[ClientStatus] = None,
        search: Optional[str] = None
    ) -> List[Client]:
        stmt = select(Client).where(Client.organization_id == org_id)

        if status:
            stmt = stmt.where(Client.status == status)

        if search:
            search_pattern = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                func.lower(Client.name).like(search_pattern) |
                func.lower(Client.client_code).like(search_pattern) |
                func.lower(Client.industry).like(search_pattern)
            )

        stmt = stmt.order_by(Client.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        org_id: str,
        client_code: str,
        name: str,
        email: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Client:
        client = Client(
            organization_id=org_id,
            client_code=client_code.upper().strip(),
            name=name.strip(),
            email=email.strip() if email else None,
            industry=industry.strip() if industry else None,
            status=ClientStatus.ACTIVE
        )
        self.db.add(client)
        await self.db.flush()
        return client

    async def update(
        self,
        client: Client,
        name: Optional[str] = None,
        email: Optional[str] = None,
        industry: Optional[str] = None,
        status: Optional[ClientStatus] = None
    ) -> Client:
        if name is not None:
            client.name = name.strip()
        if email is not None:
            client.email = email.strip() if email else None
        if industry is not None:
            client.industry = industry.strip() if industry else None
        if status is not None:
            client.status = status

        await self.db.flush()
        return client
