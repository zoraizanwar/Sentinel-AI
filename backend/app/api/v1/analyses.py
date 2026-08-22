"""Persistent Analysis REST Endpoints."""
from typing import List, Optional, Tuple
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_analyst
)
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.services.persistent_analysis_service import PersistentAnalysisService
from backend.app.schemas.persistent_analysis import (
    PersistentAnalysisResponse,
    AnalysisListItemResponse
)

router = APIRouter(prefix="/organizations/{org_id}", tags=["Analyses"])


@router.post("/clients/{client_id}/datasets/{dataset_id}/analyze", response_model=PersistentAnalysisResponse, status_code=status.HTTP_201_CREATED)
async def run_persistent_analysis(
    client_id: str,
    dataset_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_analyst),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Executes the leak-free ML pipeline on a persisted dataset, scores transactions, and stores results in the database."""
    org, _ = org_tuple
    service = PersistentAnalysisService(db)
    return await service.run_analysis(
        org_id=org.id,
        client_id=client_id,
        dataset_id=dataset_id,
        user_id=current_user.id
    )


@router.get("/analyses", response_model=List[AnalysisListItemResponse])
async def list_analyses(
    client_id: Optional[str] = Query(None, description="Optional filter by client ID"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Lists completed and historical fraud analysis runs for the organization or a specific client."""
    org, _ = org_tuple
    service = PersistentAnalysisService(db)
    return await service.list_analyses(org_id=org.id, client_id=client_id)


@router.get("/analyses/{analysis_id}", response_model=PersistentAnalysisResponse)
async def get_analysis_details(
    analysis_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Fetches details, validation metrics, test metrics, and risk distributions for a persistent analysis run."""
    org, _ = org_tuple
    service = PersistentAnalysisService(db)
    return await service.get_analysis(org_id=org.id, analysis_id=analysis_id)
