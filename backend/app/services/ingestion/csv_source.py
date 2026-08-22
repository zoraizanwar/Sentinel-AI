"""Safe CSV Data Source implementation."""
import os
from pathlib import Path
from typing import Optional
import pandas as pd

from .base import DataSource
from .validator import DatasetValidator
from ...schemas.validation import DatasetInspectionResult
from ...core.security import validate_file_path, sanitize_filename
from ...core.exceptions import IngestionError, FileValidationError


class CSVDataSource(DataSource):
    """
    CSV Data Source with strict validation, encoding fallback, and security checks.
    Preserves original data integrity without performing premature ML transformations.
    """
    
    def __init__(self, file_path: str, dataset_name: Optional[str] = None):
        self.raw_path = file_path
        self.validated_path = validate_file_path(file_path)
        self.dataset_name = sanitize_filename(dataset_name or self.validated_path.name)
        self._df: Optional[pd.DataFrame] = None
        self._validator: Optional[DatasetValidator] = None

    def load_data(self) -> pd.DataFrame:
        """
        Safely reads the CSV into memory with multi-encoding fallback.
        Does not modify, scale, encode, or alter original rows or columns.
        """
        if self._df is not None:
            return self._df
            
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        last_error = None
        
        for enc in encodings:
            try:
                # Read CSV safely
                df = pd.read_csv(self.validated_path, encoding=enc, low_memory=False)
                self._df = df
                return self._df
            except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as e:
                last_error = e
                continue
            except Exception as e:
                raise IngestionError(f"Failed to read CSV file '{self.dataset_name}': {str(e)}")
                
        raise IngestionError(
            f"Failed to parse CSV file '{self.dataset_name}' with supported encodings {encodings}. Error: {str(last_error)}",
            code="CSV_PARSE_FAILED"
        )

    def inspect(self) -> DatasetInspectionResult:
        """
        Inspects and runs complete rule-based validation on the loaded dataset.
        """
        df = self.load_data()
        file_size = self.validated_path.stat().st_size
        validator = DatasetValidator(df=df, dataset_name=self.dataset_name, file_size_bytes=file_size)
        return validator.validate()
