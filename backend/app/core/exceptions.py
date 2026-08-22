"""Sentinel AI Custom Domain Exceptions."""

class SentinelException(Exception):
    """Base exception for Sentinel AI."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


# Alias for backward compatibility
SentinelAIException = SentinelException


class FileValidationError(SentinelException):
    """Raised when file extension, size, or format is invalid."""
    def __init__(self, message: str, code: str = "FILE_VALIDATION_ERROR", status_code: int = 400):
        super().__init__(message, code=code, status_code=status_code)


class IngestionError(SentinelException):
    """Raised when dataset loading or parsing fails."""
    def __init__(self, message: str, code: str = "INGESTION_ERROR", status_code: int = 400):
        super().__init__(message, code=code, status_code=status_code)


class DatasetValidationError(SentinelException):
    """Raised when dataset fails critical schema or data quality requirements."""
    def __init__(self, message: str, code: str = "DATASET_VALIDATION_ERROR", status_code: int = 422):
        super().__init__(message, code=code, status_code=status_code)


class AnalysisNotFoundError(SentinelException):
    """Raised when an analysis session does not exist or has expired."""
    def __init__(self, message: str = "Analysis session not found or has expired.", code: str = "ANALYSIS_NOT_FOUND", status_code: int = 404):
        super().__init__(message, code=code, status_code=status_code)


class TransactionNotFoundError(SentinelException):
    """Raised when a specific transaction ID cannot be found in the active session."""
    def __init__(self, message: str = "Transaction not found in analysis session.", code: str = "TRANSACTION_NOT_FOUND", status_code: int = 404):
        super().__init__(message, code=code, status_code=status_code)


class AnalysisExecutionError(SentinelException):
    """Raised when analysis or ML training pipeline execution fails."""
    def __init__(self, message: str, code: str = "ANALYSIS_EXECUTION_ERROR", status_code: int = 500):
        super().__init__(message, code=code, status_code=status_code)


class ExplainabilityError(SentinelException):
    """Raised when SHAP explanation fails for a transaction."""
    def __init__(self, message: str, code: str = "EXPLAINABILITY_ERROR", status_code: int = 500):
        super().__init__(message, code=code, status_code=status_code)
