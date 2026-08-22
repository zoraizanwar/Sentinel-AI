"""Client Management Endpoints."""
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_analyst,
    require_org_admin
)
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.models.client import ClientStatus
from backend.app.services.client_service import ClientService
from backend.app.schemas.client import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
    ClientDashboardResponse
)

router = APIRouter(prefix="/organizations/{org_id}/clients", tags=["Clients"])


@router.get("", response_model=List[ClientResponse])
async def list_clients(
    status: Optional[ClientStatus] = Query(None, description="Filter by active/archived status"),
    search: Optional[str] = Query(None, description="Search by name, client code or industry"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Lists clients belonging to the organization with search and status filtering."""
    org, _ = org_tuple
    service = ClientService(db)
    return await service.list_clients(org_id=org.id, status=status, search=search)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_analyst),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new client within the organization (ANALYST or ADMIN required)."""
    org, _ = org_tuple
    service = ClientService(db)
    return await service.create_client(
        org_id=org.id,
        client_code=payload.client_code,
        name=payload.name,
        email=payload.email,
        industry=payload.industry,
        user_id=current_user.id
    )


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client_details(
    client_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details for a single client in the organization."""
    org, _ = org_tuple
    service = ClientService(db)
    client_repo = service.client_repo
    client = await client_repo.get_by_id(org.id, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found in this organization.")
    return ClientResponse.model_validate(client)


@router.get("/{client_id}/dashboard", response_model=ClientDashboardResponse)
async def get_client_dashboard(
    client_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves client-specific fraud analytics dashboard and risk metrics."""
    org, _ = org_tuple
    service = ClientService(db)
    return await service.get_client_dashboard(org_id=org.id, client_id=client_id)


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_analyst),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates client details (ANALYST or ADMIN required)."""
    org, _ = org_tuple
    service = ClientService(db)
    return await service.update_client(
        org_id=org.id,
        client_id=client_id,
        name=payload.name,
        email=payload.email,
        industry=payload.industry,
        status=payload.status,
        user_id=current_user.id
    )


@router.delete("/{client_id}", response_model=ClientResponse)
async def archive_client(
    client_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_admin),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Archives a client instead of hard deleting (ADMIN required)."""
    org, _ = org_tuple
    service = ClientService(db)
    return await service.update_client(
        org_id=org.id,
        client_id=client_id,
        status=ClientStatus.ARCHIVED,
        user_id=current_user.id
    )
