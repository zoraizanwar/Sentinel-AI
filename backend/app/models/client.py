"""Client Model for Multi-Client Fraud Monitoring."""
import enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, generate_uuid

if TYPE_CHECKING:
    from backend.app.models.organization import Organization
    from backend.app.models.dataset import Dataset
    from backend.app.models.analysis import Analysis
    from backend.app.models.report import Report


class ClientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Client(Base, TimestampMixin):
    __tablename__ = "clients"

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
    client_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    status: Mapped[ClientStatus] = mapped_column(
        SQLEnum(ClientStatus),
        default=ClientStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="clients"
    )
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis",
        back_populates="client",
        cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="client",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "client_code", name="uq_org_client_code"),
        Index("ix_client_org_code", "organization_id", "client_code"),
        Index("ix_client_org_status", "organization_id", "status"),
    )
