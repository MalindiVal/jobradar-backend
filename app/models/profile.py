from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.base import utcnow

class Skill(Base):
    """Référentiel de compétences, partagé entre les profils."""
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    # Clé de comparaison (minuscules, espaces réduits) : « React » et « react » sont la même compétence.
    normalized_name: Mapped[str] = mapped_column(String(100), unique=True, index=True)

class ProfileSkill(Base):
    __tablename__ = "profile_skills"
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True, index=True)
    level: Mapped[str | None] = mapped_column(String(30), nullable=True)

    skill: Mapped[Skill] = relationship(lazy="joined")

class Profile(Base):
    """Profil professionnel comparé aux offres lors de l'analyse IA."""
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    headline: Mapped[str] = mapped_column(String(200), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    skill_links: Mapped[list[ProfileSkill]] = relationship(cascade="all, delete-orphan", lazy="selectin",
                                                           order_by=ProfileSkill.skill_id)

    @property
    def skills(self) -> list[str]:
        return [link.skill.name for link in self.skill_links]
