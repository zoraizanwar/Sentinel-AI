"""Comprehensive tests for Dataset Ingestion and Validation Engine."""
import os
import pytest
import pandas as pd
import numpy as np

from backend.app.services.ingestion.csv_source import CSVDataSource
from backend.app.services.ingestion.validator import DatasetValidator
from backend.app.schemas.validation import (
    Severity,
    ValidationStatus,
    DatasetInspectionResult,
)
from backend.app.core.exceptions import FileValidationError, IngestionError


class TestDatasetIngestionAndValidation:

    # 1. Valid CSV
    def test_valid_csv_ingestion(self, temp_dir, sample_valid_df):
        file_path = os.path.join(temp_dir, "valid_data.csv")
        sample_valid_df.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        df = source.load_data()
        assert len(df) == 100
        assert list(df.columns) == list(sample_valid_df.columns)

        result = source.inspect()
        assert isinstance(result, DatasetInspectionResult)
        assert result.validation_status in [ValidationStatus.VALID, ValidationStatus.WARNINGS]
        assert result.target_column == "is_fraud"
        assert len(result.errors) == 0

    # 2. Empty CSV
    def test_empty_csv(self, temp_dir):
        file_path = os.path.join(temp_dir, "empty.csv")
        with open(file_path, "w") as f:
            f.write("")

        with pytest.raises(FileValidationError) as excinfo:
            source = CSVDataSource(file_path)
        assert "empty" in str(excinfo.value).lower()

    # 3. Invalid Extension
    def test_invalid_extension(self, temp_dir):
        file_path = os.path.join(temp_dir, "dataset.xlsx")
        with open(file_path, "w") as f:
            f.write("dummy content")

        with pytest.raises(FileValidationError) as excinfo:
            source = CSVDataSource(file_path)
        assert "unsupported file extension" in str(excinfo.value).lower()

    # 4. Missing Target Column
    def test_missing_target_column(self, temp_dir, sample_valid_df):
        df_no_target = sample_valid_df.drop(columns=["is_fraud"])
        file_path = os.path.join(temp_dir, "no_target.csv")
        df_no_target.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.validation_status == ValidationStatus.INVALID
        assert any(e.code == "MISSING_TARGET_COLUMN" for e in result.errors)

    # 5. Missing Values
    def test_missing_values_warning(self, temp_dir, sample_valid_df):
        df_missing = sample_valid_df.copy()
        df_missing.loc[0:5, "amt"] = np.nan
        file_path = os.path.join(temp_dir, "missing_vals.csv")
        df_missing.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.total_missing_cells == 6
        assert any(w.code == "MISSING_VALUES_PRESENT" for w in result.warnings)

    # 6. Duplicate Rows
    def test_duplicate_rows_warning(self, temp_dir, sample_valid_df):
        df_dups = pd.concat([sample_valid_df, sample_valid_df.iloc[:5]], ignore_index=True)
        file_path = os.path.join(temp_dir, "duplicates.csv")
        df_dups.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.duplicate_rows_count == 5
        assert any(w.code == "DUPLICATE_ROWS_FOUND" for w in result.warnings)

    # 7. Single-Class Dataset
    def test_single_class_dataset_error(self, temp_dir, sample_valid_df):
        df_single_class = sample_valid_df.copy()
        df_single_class["is_fraud"] = 0  # All legitimate
        file_path = os.path.join(temp_dir, "single_class.csv")
        df_single_class.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.validation_status == ValidationStatus.INVALID
        assert any(e.code == "SINGLE_CLASS_TARGET" for e in result.errors)

    # 8. Severe Class Imbalance
    def test_severe_class_imbalance_warning(self, temp_dir, sample_valid_df):
        # sample_valid_df has 3 frauds out of 100 rows (3%), triggering severe imbalance
        file_path = os.path.join(temp_dir, "imbalanced.csv")
        sample_valid_df.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.class_distribution.is_severely_imbalanced is True
        assert any(w.code == "SEVERE_CLASS_IMBALANCE" for w in result.warnings)

    # 9. Invalid Numeric Values (e.g. Negative Amount)
    def test_negative_transaction_amount_warning(self, temp_dir, sample_valid_df):
        df_neg_amt = sample_valid_df.copy()
        df_neg_amt.loc[0, "amt"] = -50.0
        file_path = os.path.join(temp_dir, "neg_amt.csv")
        df_neg_amt.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert any(w.code == "NEGATIVE_TRANSACTION_AMOUNT" for w in result.warnings)

    # 10. Malformed CSV Handling
    def test_malformed_csv_parsing(self, temp_dir):
        file_path = os.path.join(temp_dir, "malformed.csv")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("col1,col2,is_fraud\n")
            f.write("1,2,0\n")
            f.write("1,2,3,4,5,6,extra_cols_corrupt\n")

        source = CSVDataSource(file_path)
        try:
            source.inspect()
        except IngestionError:
            pass  # Handled safely by Sentinel ingestion layer

    # 11. Very Small Dataset (< MIN_DATASET_ROWS)
    def test_very_small_dataset_error(self, temp_dir, sample_valid_df):
        df_tiny = sample_valid_df.iloc[:10]  # Only 10 rows (< 50)
        file_path = os.path.join(temp_dir, "tiny.csv")
        df_tiny.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert result.validation_status == ValidationStatus.INVALID
        assert any(e.code == "INSUFFICIENT_ROWS" for e in result.errors)

    # 12. Constant Columns Detection
    def test_constant_column_warning(self, temp_dir, sample_valid_df):
        df_const = sample_valid_df.copy()
        df_const["constant_code"] = "STATIC_VAL"
        file_path = os.path.join(temp_dir, "const_col.csv")
        df_const.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert any(w.code == "CONSTANT_COLUMN" and w.column == "constant_code" for w in result.warnings)

    # 13. High-Cardinality Categorical Columns
    def test_high_cardinality_warning(self, temp_dir):
        n_rows = 200
        # 120 unique values in 200 rows (>100 threshold, but unique < total rows so not 1-to-1 ID)
        df_card = pd.DataFrame({
            "high_card_cat": [f"category_{i % 120}" for i in range(n_rows)],
            "amt": [10.0] * n_rows,
            "is_fraud": [1 if i < 10 else 0 for i in range(n_rows)]
        })
        file_path = os.path.join(temp_dir, "high_card.csv")
        df_card.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert any(w.code == "HIGH_CARDINALITY_FEATURE" for w in result.warnings)

    # 14. Identifier Detection
    def test_identifier_column_detection(self, temp_dir, sample_valid_df):
        file_path = os.path.join(temp_dir, "ident.csv")
        sample_valid_df.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        assert "trans_num" in result.detected_id_columns
        assert "cc_num" in result.detected_id_columns
        assert any(w.code == "IDENTIFIER_COLUMN_DETECTED" for w in result.warnings)

    # 15. File-Size Limit Enforcement
    def test_file_size_limit_enforcement(self, temp_dir, sample_valid_df):
        file_path = os.path.join(temp_dir, "size_test.csv")
        sample_valid_df.to_csv(file_path, index=False)

        # Set artificially low limit (100 bytes)
        with pytest.raises(FileValidationError) as excinfo:
            from backend.app.core.security import validate_file_path
            validate_file_path(file_path, max_size_bytes=100)
        assert "exceeds the maximum allowed limit" in str(excinfo.value)

    # 16. Dataset Inspection Response Schema Serialization
    def test_dataset_inspection_schema_serialization(self, temp_dir, sample_valid_df):
        file_path = os.path.join(temp_dir, "schema_test.csv")
        sample_valid_df.to_csv(file_path, index=False)

        source = CSVDataSource(file_path)
        result = source.inspect()
        
        # Test Pydantic JSON serialization & deserialization
        json_data = result.model_dump_json()
        assert isinstance(json_data, str)
        reconstructed = DatasetInspectionResult.model_validate_json(json_data)
        assert reconstructed.row_count == 100
        assert reconstructed.column_count == len(sample_valid_df.columns)
        assert reconstructed.target_column == "is_fraud"
