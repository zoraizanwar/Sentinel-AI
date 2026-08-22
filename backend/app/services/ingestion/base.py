"""Abstract base interface for Data Sources."""
from abc import ABC, abstractmethod
import pandas as pd
from ...schemas.validation import DatasetInspectionResult


class DataSource(ABC):
    """Abstract data source interface enabling future database/streaming extensions."""
    
    @abstractmethod
    def load_data(self) -> pd.DataFrame:
        """Loads and returns the dataset as a pandas DataFrame."""
        pass
    
    @abstractmethod
    def inspect(self) -> DatasetInspectionResult:
        """Inspects and validates the dataset, returning structured findings."""
        pass
