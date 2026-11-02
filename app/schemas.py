from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class OfferCreate(BaseModel):
    title: str = Field(min_length=2, max_length=300)
    company: str = "Entreprise non précisée"
    location: str = "Non précisée"
    contract_type: str = "Alternance"
    duration_months: int | None = None
    description: str = ""
    skills: list[str] = []
    source: str = "manual"
    source_url: str
class OfferPatch(BaseModel):
    status: str | None = None
    is_favorite: bool | None = None
class OfferRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    location: str
    contract_type: str
    duration_months: int | None
    description: str
    skills: list[str]
    source: str
    source_url: str
    match_score: int
    match_explanation: str
    status: str
    is_favorite: bool
    first_seen_at: datetime
class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    keywords: list[str]
    locations: list[str]
    skills: list[str]
    duration_months: int
    contract_type: str
class ProfileUpdate(BaseModel):
    name: str = "Recherche principale"
    keywords: list[str] = ["développeur full stack", "backend", "data engineer", "cloud", "devops"]
    locations: list[str] = ["Dijon", "Paris", "Île-de-France"]
    skills: list[str] = ["React", "Next.js", "TypeScript", "Python", "FastAPI", "C#", "ASP.NET", "PHP", "SQL", "Docker", "Git"]
    duration_months: int = 36
    contract_type: str = "Alternance"
