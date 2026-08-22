"""Analysis Execution and Retrieval API Endpoints."""
import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from ...schemas.analysis import AnalysisResult
from ...services.analysis_service import AnalysisService
from ...core.session_store import SessionStore
from ...api.deps import get_analysis_service, get_session_store
from ...core.security import sanitize_filename
from ...core.exceptions import FileValidationError, IngestionError, AnalysisNotFoundError
from ...config import settings

router = APIRouter()


@router.post(
    "/analysis/run",
    response_model=AnalysisResult,
    summary="Run Complete Fraud Analysis",
    description="Uploads a CSV dataset, executes leak-free preprocessing, candidate model training, threshold optimization, risk scoring, analytics generation, and registers an in-memory session."
)
async def run_analysis(
    file: UploadFile = File(..., description="CSV dataset for fraud detection and risk analysis"),
    service: AnalysisService = Depends(get_analysis_service)
) -> AnalysisResult:
    # 1. Validate filename and extension
    clean_filename = sanitize_filename(file.filename or "dataset.csv")
    if not clean_filename.lower().endswith(".csv"):
        raise FileValidationError(
            f"Unsupported file extension for '{clean_filename}'. Only .csv files are accepted.",
            code="INVALID_FILE_EXTENSION"
        )

    # 2. Read bytes and guard size
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

    # 3. Parse into DataFrame
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(io.BytesIO(contents), encoding=enc, low_memory=False)
            break
        except Exception:
            continue

    if df is None:
        raise IngestionError(
            f"Failed to parse CSV file '{clean_filename}'.",
            code="CSV_PARSE_FAILED"
        )

    # 4. Orchestrate full analysis
    analysis_result, session = service.run_analysis(
        df=df,
        filename=clean_filename,
        file_size_bytes=file_size
    )

    return analysis_result


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisResult,
    summary="Retrieve Analysis Result",
    description="Retrieves the Single Source of Truth AnalysisResult from the active in-memory session."
)
def get_analysis_result(
    analysis_id: str,
    store: SessionStore = Depends(get_session_store)
) -> AnalysisResult:
    session = store.get(analysis_id)
    return session.analysis_result
