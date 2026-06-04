"""
src/models.py
=============
Pydantic models used as Structured Output schemas for OpenAI API responses.

Both models share an identical field layout so that :class:`CandidateData`
(parsed from a CV) and :class:`JobOfferData` (parsed from a job offer) can be
compared field-by-field downstream.
"""

from __future__ import annotations

from pydantic import BaseModel


class CandidateData(BaseModel):
    """Structured representation of a candidate's CV."""

    seniority_level: str
    """Seniority level inferred from the CV, e.g. 'Junior', 'Mid', 'Senior'."""

    years_of_experience: float
    """Total years of professional experience."""

    hard_skills: list[str]
    """Hard / technical skills listed or inferred from the CV."""

    soft_skills: list[str]
    """Soft skills listed or inferred from the CV."""

    foreign_languages: list[str]
    """Foreign languages with proficiency level if mentioned, e.g. 'English B2'."""


class JobOfferData(BaseModel):
    """Structured representation of a job offer's requirements."""

    seniority_level: str
    """Required seniority level, e.g. 'Junior', 'Mid', 'Senior'."""

    years_of_experience: float
    """Minimum years of experience required by the offer."""

    hard_skills: list[str]
    """Required hard / technical skills."""

    soft_skills: list[str]
    """Required soft skills."""

    foreign_languages: list[str]
    """Required foreign languages with expected proficiency if stated."""


class MatchReport(BaseModel):
    """Structured match report comparing a candidate against a job offer."""

    procent_dopasowania: int
    """Overall match percentage (0–100)."""

    spelnione_wymagania: list[str]
    """Requirements from the job offer that the candidate satisfies."""

    brakujace_wymagania: list[str]
    """Requirements from the job offer that the candidate does not meet."""

    rekomendacje_zmian_w_cv: list[str]
    """Concrete tips on what to add or change in the CV to better fit this offer."""


# --- Upskilling models ---
class ResourceItem(BaseModel):
    """Single educational resource for upskilling."""
    tytul: str
    url: str
    typ_materialu: str  # e.g. Artykuł, Wideo, Dokumentacja

class SkillUpskill(BaseModel):
    """Upskilling plan for a single skill."""
    nazwa_umiejetnosci: str
    materialy: list[ResourceItem]

class UpskillPlan(BaseModel):
    """Full upskilling plan for a set of missing skills."""
    plan_nauki: list[SkillUpskill]


# --- ATS Optimization models ---
class ATSCorrection(BaseModel):
    """Single ATS optimization suggestion for a CV fragment."""
    oryginalny_fragment: str
    zoptymalizowany_fragment: str
    uzasadnienie: str

class ATSReport(BaseModel):
    """Full ATS optimization report for a CV."""
    korekty: list[ATSCorrection]
