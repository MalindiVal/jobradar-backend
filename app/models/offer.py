from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import utcnow
from app.models.source import JobSource

# Cycle de vie de l'analyse IA d'une offre (alimenté par /internal/offers/{id}/analyze).
ANALYSIS_PENDING = "pending_analysis"
ANALYSIS_DONE = "analyzed"
ANALYSIS_FAILED = "analysis_failed"

class OfferSkill(Base):
    __tablename__ = "offer_skills"
    __table_args__ = (UniqueConstraint("offer_id", "name", name="uq_offer_skill"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("job_offers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)

    def __init__(self, name: str):
        self.name = name

class JobOffer(Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        # Identification principale : identifiant fourni par la source.
        UniqueConstraint("source_id", "external_id", name="uq_job_offer_source_external_id"),
        # Repli pour les annonces sans identifiant fiable : empreinte des champs normalisés.
        UniqueConstraint("deduplication_key", name="uq_job_offer_deduplication_key"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("job_sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    company: Mapped[str] = mapped_column(String(200), default="Entreprise non précisée")
    location: Mapped[str] = mapped_column(String(200), default="Non précisée")
    contract_type: Mapped[str] = mapped_column(String(100), default="Alternance")
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    application_url: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deduplication_key: Mapped[str] = mapped_column(String(64), index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    match_explanation: Mapped[str] = mapped_column(Text, default="")
    analysis_status: Mapped[str] = mapped_column(String(30), default=ANALYSIS_PENDING, index=True)
    status: Mapped[str] = mapped_column(String(40), default="NEW", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source_ref: Mapped[JobSource] = relationship(lazy="joined")
    skill_links: Mapped[list[OfferSkill]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                         order_by=OfferSkill.id)
    skills: AssociationProxy[list[str]] = association_proxy("skill_links", "name")

    @property
    def source(self) -> str:
        return self.source_ref.name if self.source_ref else ""

    @property
    def source_url(self) -> str:
        """Ancien nom de application_url, conservé pour le frontend existant."""
        return self.application_url
