"""Report Model for Persisted Multi-Scope PDF Audit Reports."""
import enum
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now
from datetime import datetime

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.client import Client
    from backend.app.models.analysis import Analysis


class ReportType(str, enum.Enum):
    ORGANIZATION = "ORGANIZATION"
    CLIENT = "CLIENT"
    ANALYSIS = "ANALYSIS"


class Report(Base):
    __tablename__ = "reports"

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
    client_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )
    report_type: Mapped[ReportType] = mapped_column(
        SQLEnum(ReportType),
        default=ReportType.ANALYSIS,
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(
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
    generated_by: Mapped[Optional[str]] = mapped_column(
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
        back_populates="reports"
    )
    client: Mapped[Optional["Client"]] = relationship(
        "Client",
        back_populates="reports"
    )
    analysis: Mapped[Optional["Analysis"]] = relationship(
        "Analysis",
        back_populates="reports"
    )

    __table_args__ = (
        Index("ix_report_org_type", "organization_id", "report_type"),
    )
