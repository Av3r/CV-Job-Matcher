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

    poziom_stanowiska: str
    """Seniority level inferred from the CV, e.g. 'Junior', 'Mid', 'Senior'."""

    lata_doswiadczenia: int
    """Total years of professional experience."""

    umiejetnosci_twarde: list[str]
    """Hard / technical skills listed or inferred from the CV."""

    umiejetnosci_miekkie: list[str]
    """Soft skills listed or inferred from the CV."""

    jezyki_obce: list[str]
    """Foreign languages with proficiency level if mentioned, e.g. 'English B2'."""


class JobOfferData(BaseModel):
    """Structured representation of a job offer's requirements."""

    poziom_stanowiska: str
    """Required seniority level, e.g. 'Junior', 'Mid', 'Senior'."""

    lata_doswiadczenia: int
    """Minimum years of experience required by the offer."""

    umiejetnosci_twarde: list[str]
    """Required hard / technical skills."""

    umiejetnosci_miekkie: list[str]
    """Required soft skills."""

    jezyki_obce: list[str]
    """Required foreign languages with expected proficiency if stated."""
