"""Comprehensive Rule-Based Dataset Validation Engine for Sentinel AI."""
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd

from ...schemas.validation import (
    Severity,
    ValidationStatus,
    ValidationFinding,
    ColumnSummary,
    ClassDistribution,
    DatasetInspectionResult,
)
from ...config import settings


class DatasetValidator:
    """
    Production-grade Dataset Validator enforcing data quality, schema integrity,
    class distribution checks, and feature categorization without modifying original data.
    """

    # Common standard fraud target candidate names
    TARGET_CANDIDATES = [
        "is_fraud", "isfraud", "fraud", "class", "target", "label", "is_fraudulent", "fraud_label"
    ]
    
    # Identifier-like keywords
    ID_KEYWORDS = ["id", "num", "trans_num", "cc_num", "card_num", "uuid", "guid", "account", "ssn"]
    
    # Potential leakage keywords (e.g., existing heuristic rule outputs or future flags)
    LEAKAGE_KEYWORDS = ["flagged", "isflaggedfraud", "is_flagged_fraud", "chargeback", "dispute_status"]

    def __init__(
        self,
        df: pd.DataFrame,
        dataset_name: str,
        file_size_bytes: int,
        target_column: Optional[str] = None
    ):
        self.df = df
        self.dataset_name = dataset_name
        self.file_size_bytes = file_size_bytes
        self.explicit_target = target_column
        
        self.errors: List[ValidationFinding] = []
        self.warnings: List[ValidationFinding] = []
        self.infos: List[ValidationFinding] = []

    def validate(self) -> DatasetInspectionResult:
        """Executes full validation suite and compiles structured inspection result."""
        # 1. Structural Checks
        if self._check_empty_or_too_small():
            return self._build_result(status=ValidationStatus.INVALID)

        # 2. Target Column Identification & Class Distribution
        target_col, class_dist = self._validate_target()

        # 3. Column Profiling & Anomaly Detection
        columns_profile = self._profile_columns(target_col)

        # 4. Duplicate Rows
        self._check_duplicates()

        # 5. Missing Values Audit
        self._check_missing_values()

        # Determine overall status
        if len(self.errors) > 0:
            status = ValidationStatus.INVALID
        elif len(self.warnings) > 0:
            status = ValidationStatus.WARNINGS
        else:
            status = ValidationStatus.VALID

        return self._build_result(
            status=status,
            target_col=target_col,
            class_dist=class_dist,
            columns_profile=columns_profile
        )

    def _check_empty_or_too_small(self) -> bool:
        """Validates that the dataset contains adequate rows and columns."""
        row_count, col_count = self.df.shape
        
        if row_count == 0 or col_count == 0:
            self.errors.append(ValidationFinding(
                severity=Severity.ERROR,
                code="EMPTY_DATASET",
                message="The dataset contains zero rows or zero columns and cannot be processed.",
                details={"rows": row_count, "columns": col_count}
            ))
            return True

        if row_count < settings.MIN_DATASET_ROWS:
            self.errors.append(ValidationFinding(
                severity=Severity.ERROR,
                code="INSUFFICIENT_ROWS",
                message=f"Dataset contains only {row_count} rows. Sentinel AI requires at least {settings.MIN_DATASET_ROWS} rows for statistically valid fraud evaluation.",
                details={"rows": row_count, "required_min": settings.MIN_DATASET_ROWS}
            ))
            return True
            
        self.infos.append(ValidationFinding(
            severity=Severity.INFO,
            code="DIMENSIONS_VALID",
            message=f"Dataset loaded with {row_count:,} rows and {col_count} columns.",
            details={"rows": row_count, "columns": col_count}
        ))
        return False

    def _validate_target(self) -> Tuple[Optional[str], Optional[ClassDistribution]]:
        """Identifies the fraud target column and validates its classes and balance."""
        target_col = None
        
        if self.explicit_target and self.explicit_target in self.df.columns:
            target_col = self.explicit_target
        else:
            for cand in self.TARGET_CANDIDATES:
                matches = [c for c in self.df.columns if c.lower() == cand]
                if matches:
                    target_col = matches[0]
                    break

        if not target_col:
            self.errors.append(ValidationFinding(
                severity=Severity.ERROR,
                code="MISSING_TARGET_COLUMN",
                message=f"No valid fraud target column found. Expected one of: {self.TARGET_CANDIDATES}.",
                details={"available_columns": list(self.df.columns)}
            ))
            return None, None

        # Check target values
        target_series = self.df[target_col].dropna()
        unique_vals = target_series.unique()
        
        if len(unique_vals) <= 1:
            self.errors.append(ValidationFinding(
                severity=Severity.ERROR,
                code="SINGLE_CLASS_TARGET",
                message=f"Target column '{target_col}' contains only one class value ({list(unique_vals)}). Supervised fraud detection requires both legitimate and fraudulent examples.",
                column=target_col,
                details={"unique_values": [str(v) for v in unique_vals]}
            ))
            return target_col, None

        if len(unique_vals) > 2:
            self.errors.append(ValidationFinding(
                severity=Severity.ERROR,
                code="NON_BINARY_TARGET",
                message=f"Target column '{target_col}' has {len(unique_vals)} distinct values. Sentinel AI expects binary fraud labels (0 = Legitimate, 1 = Fraudulent).",
                column=target_col,
                details={"unique_values": [str(v) for v in unique_vals[:10]]}
            ))
            return target_col, None

        # Map binary values (e.g. 0/1 or False/True)
        val_counts = target_series.value_counts()
        
        # Determine 0 (legit) and 1 (fraud)
        # Typically fraud is the minority class in financial datasets
        if 0 in val_counts and 1 in val_counts:
            legit_count = int(val_counts[0])
            fraud_count = int(val_counts[1])
        else:
            sorted_counts = val_counts.sort_values(ascending=True)
            fraud_count = int(sorted_counts.iloc[0])
            legit_count = int(sorted_counts.iloc[1])

        total_count = legit_count + fraud_count
        fraud_pct = (fraud_count / total_count) * 100 if total_count > 0 else 0.0
        imbalance_ratio = round(legit_count / fraud_count, 2) if fraud_count > 0 else 0.0
        is_severely_imbalanced = (fraud_count / total_count) < settings.SEVERE_IMBALANCE_THRESHOLD

        class_dist = ClassDistribution(
            target_column=target_col,
            total_count=total_count,
            legitimate_count=legit_count,
            fraud_count=fraud_count,
            fraud_percentage=round(fraud_pct, 6),
            imbalance_ratio=imbalance_ratio,
            is_single_class=False,
            is_severely_imbalanced=is_severely_imbalanced
        )

        if is_severely_imbalanced:
            self.warnings.append(ValidationFinding(
                severity=Severity.WARNING,
                code="SEVERE_CLASS_IMBALANCE",
                message=f"Severe class imbalance detected in target '{target_col}': {fraud_count:,} fraud cases ({fraud_pct:.3f}%) vs {legit_count:,} legitimate ({imbalance_ratio}:1 ratio). Requires stratified evaluation.",
                column=target_col,
                details={"fraud_percentage": fraud_pct, "imbalance_ratio": imbalance_ratio}
            ))
        else:
            self.infos.append(ValidationFinding(
                severity=Severity.INFO,
                code="CLASS_DISTRIBUTION_OK",
                message=f"Target '{target_col}' validated: {fraud_count:,} fraud ({fraud_pct:.2f}%) and {legit_count:,} legitimate cases.",
                column=target_col
            ))

        return target_col, class_dist

    def _profile_columns(self, target_col: Optional[str]) -> Dict[str, ColumnSummary]:
        """Profiles each column for data types, cardinalities, nulls, and domain anomalies."""
        profile: Dict[str, ColumnSummary] = {}
        row_count = len(self.df)

        for col in self.df.columns:
            series = self.df[col]
            null_count = int(series.isnull().sum())
            null_pct = round((null_count / row_count) * 100, 2) if row_count > 0 else 0.0
            non_null = series.dropna()
            unique_count = int(non_null.nunique())

            is_numeric = bool(pd.api.types.is_numeric_dtype(series))
            is_datetime = bool(
                pd.api.types.is_datetime64_any_dtype(series) or
                ('time' in col.lower() or 'date' in col.lower())
            )
            is_categorical = not is_numeric and not is_datetime
            is_constant = unique_count <= 1
            is_high_cardinality = is_categorical and unique_count > settings.HIGH_CARDINALITY_THRESHOLD
            
            # Identifier candidate detection
            is_id = any(kw in col.lower() for kw in self.ID_KEYWORDS) or (
                unique_count == row_count and row_count > 100 and col != target_col
            )
            
            # Leakage candidate detection
            is_leakage = any(kw in col.lower() for kw in self.LEAKAGE_KEYWORDS) and col != target_col

            min_val = None
            max_val = None
            mean_val = None
            if is_numeric and len(non_null) > 0:
                min_val = float(non_null.min())
                max_val = float(non_null.max())
                mean_val = float(round(non_null.mean(), 4))
                
                # Check for anomalous numeric values (e.g. negative amounts)
                if ('amt' in col.lower() or 'amount' in col.lower()) and min_val < 0:
                    self.warnings.append(ValidationFinding(
                        severity=Severity.WARNING,
                        code="NEGATIVE_TRANSACTION_AMOUNT",
                        message=f"Column '{col}' contains negative values (minimum: {min_val}). Transactions typically require non-negative amounts.",
                        column=col,
                        details={"min": min_val}
                    ))

            # Sample values for preview
            sample_values = [str(x) for x in non_null.head(5).tolist()]

            # Warnings for column anomalies
            if is_constant and col != target_col:
                self.warnings.append(ValidationFinding(
                    severity=Severity.WARNING,
                    code="CONSTANT_COLUMN",
                    message=f"Column '{col}' contains only {unique_count} unique value and provides zero variance.",
                    column=col,
                    details={"unique_count": unique_count}
                ))

            if is_high_cardinality and not is_id and col != target_col:
                self.warnings.append(ValidationFinding(
                    severity=Severity.WARNING,
                    code="HIGH_CARDINALITY_FEATURE",
                    message=f"Categorical column '{col}' has {unique_count:,} unique categories. Requires domain frequency encoding or high-cardinality handling.",
                    column=col,
                    details={"unique_count": unique_count}
                ))

            if is_id and col != target_col:
                self.warnings.append(ValidationFinding(
                    severity=Severity.WARNING,
                    code="IDENTIFIER_COLUMN_DETECTED",
                    message=f"Column '{col}' detected as a transaction/entity identifier ({unique_count:,} unique values). Must be retained as metadata and excluded from direct model feature matrices.",
                    column=col,
                    details={"unique_count": unique_count}
                ))

            if is_leakage:
                self.warnings.append(ValidationFinding(
                    severity=Severity.WARNING,
                    code="POTENTIAL_TARGET_LEAKAGE",
                    message=f"Column '{col}' matches heuristic rule / target leakage keywords. Must be excluded from predictive training.",
                    column=col
                ))

            profile[col] = ColumnSummary(
                name=col,
                dtype=str(series.dtype),
                non_null_count=row_count - null_count,
                null_count=null_count,
                null_percentage=null_pct,
                unique_count=unique_count,
                is_numeric=is_numeric,
                is_categorical=is_categorical,
                is_datetime=is_datetime,
                is_constant=is_constant,
                is_high_cardinality=is_high_cardinality,
                is_identifier_candidate=is_id,
                is_leakage_candidate=is_leakage,
                min_value=min_val,
                max_value=max_val,
                mean_value=mean_val,
                sample_values=sample_values
            )

        return profile

    def _check_duplicates(self) -> None:
        """Audits exact duplicate rows."""
        dup_count = int(self.df.duplicated().sum())
        if dup_count > 0:
            dup_pct = (dup_count / len(self.df)) * 100
            self.warnings.append(ValidationFinding(
                severity=Severity.WARNING,
                code="DUPLICATE_ROWS_FOUND",
                message=f"Dataset contains {dup_count:,} exact duplicate rows ({dup_pct:.2f}%).",
                details={"duplicate_count": dup_count, "duplicate_percentage": round(dup_pct, 4)}
            ))
        else:
            self.infos.append(ValidationFinding(
                severity=Severity.INFO,
                code="ZERO_DUPLICATES",
                message="Dataset verified with 0 duplicate rows."
            ))

    def _check_missing_values(self) -> None:
        """Audits missing values across the entire dataset."""
        total_missing = int(self.df.isnull().sum().sum())
        total_cells = self.df.shape[0] * self.df.shape[1]
        
        if total_missing > 0:
            missing_pct = (total_missing / total_cells) * 100
            self.warnings.append(ValidationFinding(
                severity=Severity.WARNING,
                code="MISSING_VALUES_PRESENT",
                message=f"Dataset contains {total_missing:,} missing cells ({missing_pct:.2f}% of total data cells). Imputation required during preprocessing.",
                details={"total_missing": total_missing, "missing_percentage": round(missing_pct, 4)}
            ))
        else:
            self.infos.append(ValidationFinding(
                severity=Severity.INFO,
                code="ZERO_MISSING_VALUES",
                message="Dataset verified complete with 0 missing values across all columns."
            ))

    def _build_result(
        self,
        status: ValidationStatus,
        target_col: Optional[str] = None,
        class_dist: Optional[ClassDistribution] = None,
        columns_profile: Optional[Dict[str, ColumnSummary]] = None
    ) -> DatasetInspectionResult:
        """Constructs the complete inspection result payload."""
        columns_profile = columns_profile or {}
        
        detected_numeric = [c for c, p in columns_profile.items() if p.is_numeric and c != target_col]
        detected_categorical = [c for c, p in columns_profile.items() if p.is_categorical and c != target_col]
        detected_temporal = [c for c, p in columns_profile.items() if p.is_datetime]
        detected_amount = [c for c in columns_profile.keys() if ('amt' in c.lower() or 'amount' in c.lower()) and c != target_col]
        detected_id = [c for c, p in columns_profile.items() if p.is_identifier_candidate]
        potential_leakage = [c for c, p in columns_profile.items() if p.is_leakage_candidate]
        
        dup_count = int(self.df.duplicated().sum()) if len(self.df) > 0 else 0
        total_missing = int(self.df.isnull().sum().sum()) if len(self.df) > 0 else 0

        return DatasetInspectionResult(
            dataset_name=self.dataset_name,
            file_size_bytes=self.file_size_bytes,
            row_count=len(self.df),
            column_count=len(self.df.columns),
            target_column=target_col,
            validation_status=status,
            errors=self.errors,
            warnings=self.warnings,
            infos=self.infos,
            columns=columns_profile,
            class_distribution=class_dist,
            detected_numeric_columns=detected_numeric,
            detected_categorical_columns=detected_categorical,
            detected_temporal_columns=detected_temporal,
            detected_amount_columns=detected_amount,
            detected_id_columns=detected_id,
            potential_leakage_columns=potential_leakage,
            duplicate_rows_count=dup_count,
            total_missing_cells=total_missing
        )
