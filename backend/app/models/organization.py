"""Organization and OrganizationMember Models for Tenant Isolation and RBAC."""
import enum
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin, generate_uuid, utc_now
from datetime import datetime

if TYPE_CHECKING:
    from backend.app.models.user import User
    from backend.app.models.client import Client
    from backend.app.models.dataset import Dataset
    from backend.app.models.analysis import Analysis
    from backend.app.models.report import Report
    from backend.app.models.audit_log import AuditLog


class OrganizationRole(str, enum.Enum):
    ORGANIZATION_ADMIN = "ORGANIZATION_ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    clients: Mapped[List["Client"]] = relationship(
        "Client",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    datasets: Mapped[List["Dataset"]] = relationship(
        "Dataset",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    analyses: Mapped[List["Analysis"]] = relationship(
        "Analysis",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="organization",
        cascade="all, delete-orphan"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="organization",
        cascade="all, delete-orphan"
    )


class OrganizationMember(Base):
    __tablename__ = "organization_members"

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
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role: Mapped[OrganizationRole] = mapped_column(
        SQLEnum(OrganizationRole),
        default=OrganizationRole.VIEWER,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="members"
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="memberships",
        lazy="joined"
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_org_user_membership"),
        Index("ix_org_member_org_user", "organization_id", "user_id"),
    )
