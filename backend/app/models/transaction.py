"""Transaction Model for High-Performance Paginated Fraud Exploration."""
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now
from datetime import datetime

if TYPE_CHECKING:
    from backend.app.models.analysis import Analysis


class Transaction(Base):
    __tablename__ = "transactions"

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
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transaction_num: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    timestamp: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )
    merchant: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
    )
    lat: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    long: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    merch_lat: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    merch_long: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True
    )
    
    # Model Predictions & Scoring
    is_fraud_pred: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True
    )
    actual_fraud_label: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        index=True
    )
    fraud_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )
    risk_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )
    risk_band: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationships
    analysis: Mapped["Analysis"] = relationship(
        "Analysis",
        back_populates="transactions"
    )

    __table_args__ = (
        Index("ix_tx_analysis_risk_score", "analysis_id", "risk_score"),
        Index("ix_tx_analysis_risk_band", "analysis_id", "risk_band"),
        Index("ix_tx_analysis_amount", "analysis_id", "amount"),
        Index("ix_tx_analysis_fraud", "analysis_id", "is_fraud_pred"),
        Index("ix_tx_org_client_analysis", "organization_id", "client_id", "analysis_id"),
    )
