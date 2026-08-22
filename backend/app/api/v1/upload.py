"""Dataset Pre-flight Inspection API Endpoint."""
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from ...schemas.validation import DatasetInspectionResult
from ...services.analysis_service import AnalysisService
from ...api.deps import get_analysis_service
from ...core.security import sanitize_filename
from ...core.exceptions import FileValidationError, IngestionError
from ...config import settings

router = APIRouter()


@router.post(
    "/dataset/inspect",
    response_model=DatasetInspectionResult,
    summary="Inspect & Pre-validate Dataset",
    description="Uploads a CSV dataset and returns a comprehensive structural, class distribution, and data quality inspection report without training models."
)
async def inspect_dataset(
    file: UploadFile = File(..., description="CSV dataset file to inspect"),
    service: AnalysisService = Depends(get_analysis_service)
) -> DatasetInspectionResult:
    # 1. Validate file extension
    clean_filename = sanitize_filename(file.filename or "uploaded_dataset.csv")
    if not clean_filename.lower().endswith(".csv"):
        raise FileValidationError(
            f"Unsupported file extension for '{clean_filename}'. Only .csv files are supported.",
            code="INVALID_FILE_EXTENSION"
        )

    # 2. Read file content with size limit guard
    contents = await file.read()
    file_size = len(contents)

    if file_size == 0:
        raise FileValidationError("Uploaded CSV file is empty (0 bytes).", code="EMPTY_FILE")

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise FileValidationError(
            f"File size exceeds maximum allowed limit of {max_mb:.0f} MB.",
            code="FILE_TOO_LARGE",
            status_code=413
        )

    # 3. Safely parse into pandas DataFrame
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    df = None
    last_err = None

    for enc in encodings:
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=enc, low_memory=False)
            break
        except Exception as e:
            last_err = e
            continue

    if df is None:
        raise IngestionError(
            f"Could not parse CSV file '{clean_filename}'. Please check file formatting.",
            code="CSV_PARSE_FAILED"
        )

    # 4. Execute Rule-Based Inspection
    return service.inspect_dataset(df=df, filename=clean_filename, file_size_bytes=file_size)
