"""Organization & Member Management Endpoints."""
from typing import List, Tuple
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_admin
)
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.services.org_service import OrganizationService
from backend.app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationMemberResponse,
    AddMemberRequest,
    OrgDashboardResponse
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Lists all organizations the current authenticated user belongs to."""
    service = OrganizationService(db)
    return await service.list_user_organizations(current_user.id)


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Creates a new organization and assigns the creator as ORGANIZATION_ADMIN."""
    service = OrganizationService(db)
    return await service.create_organization(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description
    )


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization_details(
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details for an organization (Strict Tenant Isolation enforced)."""
    org, member = org_tuple
    service = OrganizationService(db)
    return await service.get_organization(org.id, current_user.id)


@router.get("/{org_id}/dashboard", response_model=OrgDashboardResponse)
async def get_organization_dashboard(
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves organization-level fraud KPIs, high-risk clients comparison, and recent activity."""
    org, _ = org_tuple
    service = OrganizationService(db)
    return await service.get_organization_dashboard(org.id)


@router.get("/{org_id}/members", response_model=List[OrganizationMemberResponse])
async def list_organization_members(
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Lists all active members in the organization."""
    org, _ = org_tuple
    service = OrganizationService(db)
    return await service.list_members(org.id)


@router.post("/{org_id}/members", response_model=OrganizationMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    payload: AddMemberRequest,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_admin),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Adds a new member to the organization (ORGANIZATION_ADMIN required)."""
    org, _ = org_tuple
    service = OrganizationService(db)
    return await service.add_member(
        org_id=org.id,
        email=payload.email,
        role=payload.role,
        acting_user_id=current_user.id
    )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    user_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_admin),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Removes a member from the organization (ORGANIZATION_ADMIN required)."""
    org, _ = org_tuple
    service = OrganizationService(db)
    await service.remove_member(
        org_id=org.id,
        target_user_id=user_id,
        acting_user_id=current_user.id
    )
