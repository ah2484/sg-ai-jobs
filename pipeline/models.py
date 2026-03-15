"""Pydantic models for the pipeline."""

from pydantic import BaseModel, Field


class MomOccupation(BaseModel):
    """Occupation from MOM Occupational Wage Survey."""

    title: str
    slug: str
    ssoc_code: str
    category: str  # e.g. "professionals"
    category_label: str  # e.g. "Professionals"
    major_group: int = Field(ge=1, le=9)
    pay_monthly: int
    pay_annual: int
    pay_p25: int | None = None
    pay_p75: int | None = None


class SkillsFutureRole(BaseModel):
    """Role from SkillsFuture database."""

    title: str
    sector: str
    tasks: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class Occupation(BaseModel):
    """Enriched occupation combining MOM + SkillsFuture data."""

    title: str
    slug: str
    ssoc_code: str
    category: str
    category_label: str
    major_group: int = Field(ge=1, le=9)
    sector: str | None = None
    pay_monthly: int
    pay_annual: int
    pay_p25: int | None = None
    pay_p75: int | None = None
    tasks: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    skillsfuture_funded: bool = False
    ep_spass_share: float | None = None


class ScoredOccupation(Occupation):
    """Occupation with AI exposure score."""

    exposure: int = Field(ge=0, le=10)
    exposure_rationale: str = ""
