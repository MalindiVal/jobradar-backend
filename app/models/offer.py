from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.associationproxy import association_proxy, AssociationProxy
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import utcnow
from app.models.source import Source

class OfferSkill(Base):
    __tablename__ = "offer_skills"
    __table_args__ = (UniqueConstraint("offer_id", "name", name="uq_offer_skill"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)

    def __init__(self, name: str):
        self.name = name

class Offer(Base):
    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("deduplication_key", name="uq_offer_deduplication_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(300), index=True)
    company: Mapped[str] = mapped_column(String(200), default="Entreprise non précisée")
    location: Mapped[str] = mapped_column(String(200), default="Non précisée")
    contract_type: Mapped[str] = mapped_column(String(100), default="Alternance")
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    source_url: Mapped[str] = mapped_column(Text)
    deduplication_key: Mapped[str] = mapped_column(String(64), index=True)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    match_explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="NEW", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    source_ref: Mapped[Source] = relationship(lazy="joined")
    skill_links: Mapped[list[OfferSkill]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                         order_by=OfferSkill.id)
    skills: AssociationProxy[list[str]] = association_proxy("skill_links", "name")

    @property
    def source(self) -> str:
        return self.source_ref.name if self.source_ref else ""
