from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from app.models.base import utcnow

class JobAnalysis(Base):
    """Résultat d'une analyse Claude d'une offre au regard d'un profil (format du §6)."""
    __tablename__ = "job_analyses"
    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("job_offers.id", ondelete="CASCADE"), index=True)
    profile_id: Mapped[int | None] = mapped_column(ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    score: Mapped[int] = mapped_column(Integer)
    contract_match: Mapped[bool] = mapped_column(Boolean, default=False)
    skills_match: Mapped[list] = mapped_column(JSON, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, default=list)
    recommendation: Mapped[str] = mapped_column(String(20), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    # Détail des critères explicites ayant servi au calcul du score.
    score_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    model: Mapped[str] = mapped_column(String(100), default="")
    raw_response: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
