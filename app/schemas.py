from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

ApplicationStatus = Literal["TO_APPLY", "APPLIED", "INTERVIEW", "OFFER", "ACCEPTED", "REJECTED", "WITHDRAWN"]

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

    @field_validator("skills", mode="before")
    @classmethod
    def _skills_as_list(cls, value):
        return list(value or [])
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
class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    label: str
    base_url: str
    is_enabled: bool
class SourcePatch(BaseModel):
    label: str | None = None
    base_url: str | None = None
    is_enabled: bool | None = None
class ApplicationCreate(BaseModel):
    offer_id: int
    status: ApplicationStatus = "TO_APPLY"
    applied_at: datetime | None = None
    notes: str = ""
class ApplicationPatch(BaseModel):
    status: ApplicationStatus | None = None
    applied_at: datetime | None = None
    notes: str | None = None
class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    offer_id: int
    status: str
    applied_at: datetime | None
    notes: str
    created_at: datetime
    updated_at: datetime
    offer: OfferRead
class CollectionLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: str
    status: str
    found_count: int
    new_count: int
    error_message: str
    started_at: datetime
    finished_at: datetime | None
