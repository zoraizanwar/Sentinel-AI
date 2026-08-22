"""Analysis Model for Persistent Machine Learning & Fraud Evaluation Runs."""
import enum
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now
from datetime import datetime

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.client import Client
    from backend.app.models.dataset import Dataset
    from backend.app.models.transaction import Transaction
    from backend.app.models.report import Report


class AnalysisStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PROCESSING = "PROCESSING"


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    organization_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    client_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Model Metadata
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    optimal_threshold: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    execution_time_seconds: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus),
        default=AnalysisStatus.COMPLETED,
        nullable=False,
        index=True
    )

    # Core Structured Metrics (JSON)
    validation_metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    test_metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    fraud_statistics: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    risk_statistics: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    category_breakdown: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False
    )
    empirical_findings: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False
    )
    recommendations: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False
    )
    global_feature_importance: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="analyses"
    )
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="analyses"
    )
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="analyses"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="analysis",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_analysis_org_client", "organization_id", "client_id"),
        Index("ix_analysis_created", "created_at"),
    )
