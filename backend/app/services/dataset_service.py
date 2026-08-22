"""Dataset Upload, Validation and Local Filesystem Persistence Service."""
import os
import uuid
import pandas as pd
from typing import List, Optional, Tuple
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings
from backend.app.core.exceptions import SentinelAIException
from backend.app.core.security import sanitize_filename, validate_file_size
from backend.app.models.dataset import Dataset, DatasetValidationStatus, DatasetProcessingStatus
from backend.app.repositories.dataset_repo import DatasetRepository
from backend.app.repositories.client_repo import ClientRepository
from backend.app.services.ingestion.csv_source import CSVDataSource
from backend.app.services.ingestion.validator import DatasetValidator
from backend.app.services.audit_service import AuditService
from backend.app.schemas.dataset import DatasetResponse


class DatasetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.client_repo = ClientRepository(db)
        self.audit_service = AuditService(db)

    async def list_client_datasets(self, org_id: str, client_id: str) -> List[DatasetResponse]:
        datasets = await self.dataset_repo.list_by_client(org_id, client_id)
        return [DatasetResponse.model_validate(d) for d in datasets]

    async def get_dataset(self, org_id: str, dataset_id: str) -> DatasetResponse:
        dataset = await self.dataset_repo.get_by_id(org_id, dataset_id)
        if not dataset:
            raise SentinelAIException("Dataset not found.", status_code=404, code="DATASET_NOT_FOUND")
        return DatasetResponse.model_validate(dataset)

    async def upload_and_validate(
        self,
        org_id: str,
        client_id: str,
        upload_file: UploadFile,
        user_id: Optional[str] = None
    ) -> Tuple[DatasetResponse, dict]:
        # 1. Verify Client belongs to Organization
        client = await self.client_repo.get_by_id(org_id, client_id)
        if not client:
            raise SentinelAIException("Client not found in this organization.", status_code=404, code="CLIENT_NOT_FOUND")

        # 2. Validate filename and extension
        safe_name = sanitize_filename(upload_file.filename or "dataset.csv")
        ext = os.path.splitext(safe_name)[1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise SentinelAIException(f"Unsupported file extension '{ext}'. Only CSV is supported.", status_code=400, code="INVALID_FILE_EXTENSION")

        # 3. Read content and validate size
        content = await upload_file.read()
        validate_file_size(len(content))

        # 4. Prepare safe filesystem destination
        dest_dir = os.path.join(settings.UPLOAD_BASE_DIR, "organizations", org_id, "clients", client_id, "datasets")
        os.makedirs(dest_dir, exist_ok=True)
        unique_file_id = str(uuid.uuid4())[:8]
        file_path = os.path.join(dest_dir, f"{unique_file_id}_{safe_name}")

        with open(file_path, "wb") as f:
            f.write(content)

        # 5. Ingest and Validate with Sentinel AI Ingestion Engine
        try:
            csv_source = CSVDataSource(file_path=file_path)
            raw_df = csv_source.load_data()
            inspection_result = csv_source.inspect()
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise SentinelAIException(f"Failed to parse and validate CSV: {str(e)}", status_code=400, code="INGESTION_ERROR")

        val_status_map = {
            "VALID": DatasetValidationStatus.VALID,
            "WARNINGS": DatasetValidationStatus.WARNINGS,
            "INVALID": DatasetValidationStatus.INVALID
        }
        status_enum = val_status_map.get(inspection_result.validation_status.value, DatasetValidationStatus.VALID)

        # 6. Persist Dataset Record
        dataset = await self.dataset_repo.create(
            org_id=org_id,
            client_id=client_id,
            filename=safe_name,
            file_path=file_path,
            file_size_bytes=len(content),
            row_count=inspection_result.row_count,
            column_count=inspection_result.column_count,
            target_column=inspection_result.target_column,
            validation_status=status_enum,
            validation_summary=inspection_result.model_dump(),
            uploaded_by=user_id
        )

        await self.audit_service.log_event(
            org_id=org_id,
            action="DATASET_UPLOADED",
            resource_type="DATASET",
            resource_id=dataset.id,
            user_id=user_id,
            details={
                "filename": safe_name,
                "rows": inspection_result.row_count,
                "validation_status": status_enum.value
            }
        )
        await self.db.commit()

        return DatasetResponse.model_validate(dataset), inspection_result.model_dump()
