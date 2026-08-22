"""Dataset Model for Persisted Uploads and Pre-Flight Validation Metadata."""
import enum
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from sqlalchemy import String, Integer, BigInteger, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now
from datetime import datetime

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.client import Client
    from backend.app.models.analysis import Analysis


class DatasetValidationStatus(str, enum.Enum):
    VALID = "VALID"
    WARNINGS = "WARNINGS"
    INVALID = "INVALID"


class DatasetProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"


class Dataset(Base):
    __tablename__ = "datasets"

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
    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    file_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False
    )
    row_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    column_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    target_column: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    validation_status: Mapped[DatasetValidationStatus] = mapped_column(
        SQLEnum(DatasetValidationStatus),
        default=DatasetValidationStatus.VALID,
        nullable=False,
        index=True
    )
    validation_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    processing_status: Mapped[DatasetProcessingStatus] = mapped_column(
        SQLEnum(DatasetProcessingStatus),
        default=DatasetProcessingStatus.PENDING,
        nullable=False,
        index=True
    )
    uploaded_by: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False,
        index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="datasets"
    )
    client: Mapped["Client"] = relationship(
        "Client",
        back_populates="datasets"
    )
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_dataset_org_client", "organization_id", "client_id"),
    )
