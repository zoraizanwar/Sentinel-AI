"""Dataset Ingestion & Management Endpoints."""
from typing import List, Tuple
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import (
    get_current_user,
    require_org_member,
    require_org_analyst
)
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember
from backend.app.services.dataset_service import DatasetService
from backend.app.schemas.dataset import DatasetResponse

router = APIRouter(prefix="/organizations/{org_id}", tags=["Datasets"])


@router.post("/clients/{client_id}/datasets/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_client_dataset(
    client_id: str,
    file: UploadFile = File(..., description="CSV dataset to upload"),
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_analyst),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a client CSV dataset, executes pre-flight data quality validation, and persists metadata."""
    org, _ = org_tuple
    service = DatasetService(db)
    dataset_dto, _ = await service.upload_and_validate(
        org_id=org.id,
        client_id=client_id,
        upload_file=file,
        user_id=current_user.id
    )
    return dataset_dto


@router.get("/clients/{client_id}/datasets", response_model=List[DatasetResponse])
async def list_client_datasets(
    client_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Lists all datasets uploaded for a specific client."""
    org, _ = org_tuple
    service = DatasetService(db)
    return await service.list_client_datasets(org_id=org.id, client_id=client_id)


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset_details(
    dataset_id: str,
    org_tuple: Tuple[Organization, OrganizationMember] = Depends(require_org_member),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves dataset details and data quality findings."""
    org, _ = org_tuple
    service = DatasetService(db)
    return await service.get_dataset(org_id=org.id, dataset_id=dataset_id)
