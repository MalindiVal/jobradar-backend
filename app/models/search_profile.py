from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SearchProfile(Base):
    __tablename__ = "search_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(120), default="Recherche principale")
    keywords: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    duration_months: Mapped[int] = mapped_column(Integer, default=36)
    contract_type: Mapped[str] = mapped_column(String(100), default="Alternance")
