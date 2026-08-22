"""Thread-Safe In-Memory Session Store for Sentinel AI (No External Database).
Maintains analysis sessions, trained model artifacts, predictions DataFrames,
and SHAP caches with automated TTL expiration.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Any, List
import threading
import uuid
import pandas as pd

from ..schemas.analysis import AnalysisResult
from ..schemas.validation import DataQualityReport
from ..schemas.explainability import LocalExplanation
from ..core.exceptions import AnalysisNotFoundError
from ..config import settings


@dataclass
class AnalysisSession:
    """In-memory state capsule for an active dataset analysis."""
    analysis_id: str
    created_at: datetime
    expires_at: datetime
    raw_filename: str
    dataset: pd.DataFrame
    validation_report: DataQualityReport
    preprocessor_pipeline: Any
    trained_model: Any
    model_name: str
    optimal_threshold: float
    feature_names: List[str]
    predictions_df: pd.DataFrame
    analysis_result: AnalysisResult
    shap_explainer: Optional[Any] = None
    shap_cache: Dict[str, LocalExplanation] = field(default_factory=dict)

    @property
    def result(self) -> AnalysisResult:
        return self.analysis_result

    @property
    def explainer(self) -> Optional[Any]:
        return self.shap_explainer

    def is_expired(self) -> bool:
        """Checks if session has exceeded its TTL."""
        now = datetime.now(timezone.utc)
        # Handle timezone-aware or naive datetimes cleanly
        exp = self.expires_at if self.expires_at.tzinfo is not None else self.expires_at.replace(tzinfo=timezone.utc)
        return now > exp


class SessionStore:
    """
    Thread-safe in-memory store for AnalysisSessions.
    Implements TTL expiration without any database persistence.
    """

    def __init__(self, default_ttl_seconds: Optional[int] = None):
        self._sessions: Dict[str, AnalysisSession] = {}
        self._lock = threading.RLock()
        self.default_ttl_seconds = default_ttl_seconds or settings.SESSION_TTL_SECONDS

    def create(
        self,
        raw_filename: str,
        dataset: pd.DataFrame,
        validation_report: DataQualityReport,
        preprocessor_pipeline: Any,
        trained_model: Any,
        model_name: str,
        optimal_threshold: float,
        feature_names: List[str],
        predictions_df: pd.DataFrame,
        analysis_result: AnalysisResult,
        shap_explainer: Optional[Any] = None,
        ttl_seconds: Optional[int] = None
    ) -> AnalysisSession:
        """Creates a new session, assigns a UUID4 analysis_id, and registers it in memory."""
        analysis_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc)
        ttl = ttl_seconds or self.default_ttl_seconds
        expires_at = created_at + timedelta(seconds=ttl)

        # Set analysis_id in the AnalysisResult schema
        analysis_result.analysis_id = analysis_id
        analysis_result.created_at = created_at

        session = AnalysisSession(
            analysis_id=analysis_id,
            created_at=created_at,
            expires_at=expires_at,
            raw_filename=raw_filename,
            dataset=dataset,
            validation_report=validation_report,
            preprocessor_pipeline=preprocessor_pipeline,
            trained_model=trained_model,
            model_name=model_name,
            optimal_threshold=optimal_threshold,
            feature_names=feature_names,
            predictions_df=predictions_df,
            analysis_result=analysis_result,
            shap_explainer=shap_explainer,
            shap_cache={}
        )

        with self._lock:
            self._sessions[analysis_id] = session

        return session

    def put(self, session: AnalysisSession) -> None:
        """Registers a pre-constructed session in memory."""
        with self._lock:
            self._sessions[session.analysis_id] = session

    def get(self, analysis_id: str) -> AnalysisSession:
        """
        Retrieves a valid, unexpired session by analysis_id.
        Raises AnalysisNotFoundError if session does not exist or has expired.
        """
        with self._lock:
            session = self._sessions.get(analysis_id)
            if session is None:
                raise AnalysisNotFoundError(f"Analysis session '{analysis_id}' not found.")

            if session.is_expired():
                # Prune expired session
                del self._sessions[analysis_id]
                raise AnalysisNotFoundError(f"Analysis session '{analysis_id}' has expired.")

            return session

    def delete(self, analysis_id: str) -> bool:
        """Deletes a session from memory."""
        with self._lock:
            if analysis_id in self._sessions:
                del self._sessions[analysis_id]
                return True
            return False

    def contains(self, analysis_id: str) -> bool:
        """Checks whether a valid non-expired session exists."""
        with self._lock:
            if analysis_id not in self._sessions:
                return False
            session = self._sessions[analysis_id]
            if session.is_expired():
                del self._sessions[analysis_id]
                return False
            return True

    def cleanup_expired(self) -> int:
        """Prunes all expired sessions from memory."""
        with self._lock:
            now = datetime.now(timezone.utc)
            expired_keys = [
                k for k, s in self._sessions.items()
                if now > (s.expires_at if s.expires_at.tzinfo is not None else s.expires_at.replace(tzinfo=timezone.utc))
            ]
            for k in expired_keys:
                del self._sessions[k]
            return len(expired_keys)

    def count(self) -> int:
        """Returns the number of active sessions."""
        with self._lock:
            return len(self._sessions)

    def clear(self) -> None:
        """Clears all sessions from memory."""
        with self._lock:
            self._sessions.clear()


# Global Singleton Session Store for the FastAPI application
session_store = SessionStore()
