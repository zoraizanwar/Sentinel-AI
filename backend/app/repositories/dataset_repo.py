"""Dataset Repository for Persistent Upload Tracking."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.dataset import Dataset, DatasetValidationStatus, DatasetProcessingStatus


class DatasetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: str, dataset_id: str) -> Optional[Dataset]:
        stmt = select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.organization_id == org_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_client(self, org_id: str, client_id: str) -> List[Dataset]:
        stmt = (
            select(Dataset)
            .where(
                Dataset.organization_id == org_id,
                Dataset.client_id == client_id
            )
            .order_by(Dataset.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self,
        org_id: str,
        client_id: str,
        filename: str,
        file_path: str,
        file_size_bytes: int,
        row_count: int,
        column_count: int,
        target_column: Optional[str],
        validation_status: DatasetValidationStatus,
        validation_summary: Optional[dict],
        uploaded_by: Optional[str] = None
    ) -> Dataset:
        dataset = Dataset(
            organization_id=org_id,
            client_id=client_id,
            filename=filename,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            row_count=row_count,
            column_count=column_count,
            target_column=target_column,
            validation_status=validation_status,
            validation_summary=validation_summary,
            processing_status=DatasetProcessingStatus.PENDING,
            uploaded_by=uploaded_by
        )
        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def update_status(self, dataset: Dataset, status: DatasetProcessingStatus) -> Dataset:
        dataset.processing_status = status
        await self.db.flush()
        return dataset
