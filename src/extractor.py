"""
src/extractor.py
================
LLM-powered structured data extractor backed by the OpenAI Structured Outputs
API (``client.beta.chat.completions.parse``).

Design notes
------------
* A single ``OpenAI`` client is created once in ``__init__``.
* Both extraction methods share the same private ``_parse`` helper to avoid
  duplicated boilerplate.
* System prompts are written to behave like a strict, no-nonsense recruiter so
  the model returns only what is explicitly stated (or clearly inferable) in the
  supplied text, rather than hallucinating plausible-sounding entries.
"""

from __future__ import annotations

import logging
import os

from openai import OpenAI

from src.models import CandidateData, JobOfferData

logger = logging.getLogger(__name__)

_CV_SYSTEM_PROMPT = """\
Jesteś surowym i precyzyjnym rekruterem technicznym z wieloletnim doświadczeniem.
Twoim zadaniem jest wyciągnięcie ustrukturyzowanych danych z dostarczonego tekstu CV.

KRYTYCZNA INSTRUKCJA: Musisz przeanalizować CAŁY tekst, w tym opisy poprzednich stanowisk
i projektów, aby wyciągnąć ukryte umiejętności twarde i miękkie.
Nie ograniczaj się tylko do sekcji 'Umiejętności'.

Zasady:
- Wyciągaj WYŁĄCZNIE informacje, które jawnie wynikają z tekstu. Nie domyślaj się.
- Jeśli dana informacja nie jest dostępna, użyj wartości domyślnej:
  - str → pusty string ""
  - float → 0.0
  - list[str] → pusta lista []
- Dla pola `poziom_stanowiska` użyj jednej z wartości: "Junior", "Mid", "Senior", "Lead", "Principal".
  Określ go na podstawie całości CV (tytuły, lata doświadczenia, zakres odpowiedzialności).
- Dla pola `lata_doswiadczenia` podaj łączną liczbę lat doświadczenia zawodowego jako liczbę
  zmiennoprzecinkową (np. 2.5 dla dwóch i pół roku).
- Dla pola `znane_jezyki` uwzględniaj WSZYSTKIE języki wymienione w tekście.
  W polu 'znane_jezyki' MUSISZ bezwzględnie umieścić język ojczysty kandydata (np. Polski),
  jeśli tylko pojawia się w tekście. Nigdy go nie pomijaj.
  Jeśli poziom biegłości jest podany (np. B2, C1, native), dołącz go do nazwy języka,
  np. "Angielski C1", "Polski (native)" jeśli tak wskazuje tekst.
"""

_JOB_SYSTEM_PROMPT = """\
Jesteś surowym i precyzyjnym rekruterem technicznym z wieloletnim doświadczeniem.
Twoim zadaniem jest wyciągnięcie ustrukturyzowanych wymagań z dostarczonego tekstu oferty pracy.

Zasady:
- Wyciągaj WYŁĄCZNIE wymagania, które jawnie wynikają z tekstu. Nie domyślaj się.
- Jeśli dana informacja nie jest dostępna, użyj wartości domyślnej:
  - str → pusty string ""
  - int → 0
  - list[str] → pusta lista []
- Dla pola `poziom_stanowiska` użyj jednej z wartości: "Junior", "Mid", "Senior", "Lead", "Principal".
  Wyznacz go na podstawie tytułu stanowiska i wymagań.
- Dla pola `lata_doswiadczenia` podaj minimalną liczbę wymaganych lat doświadczenia jako liczbę
  zmiennoprzecinkową (np. 3.0).
- Dla pola `znane_jezyki` uwzględniaj tylko języki wymienione jako wymaganie lub atut.
  Dołącz poziom biegłości jeśli jest podany, np. "Angielski B2".
"""


class DataExtractor:
    """
    Extracts structured data from plain text using the OpenAI Structured Outputs API.

    Parameters
    ----------
    model:
        OpenAI model identifier to use for all calls.  Defaults to
        ``"gpt-4o-mini"``.

    Raises
    ------
    ValueError
        If the ``OPENAI_API_KEY`` environment variable is not set.
    """

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is not set. "
                "Create a .env file with OPENAI_API_KEY=<your-key> and load it "
                "before constructing DataExtractor."
            )
        self._model = model
        self._client = OpenAI(api_key=api_key)
        logger.info("DataExtractor initialized with model=%s", model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_cv(self, text: str) -> CandidateData:
        """
        Extract structured candidate data from an anonymized CV text.

        Parameters
        ----------
        text:
            Plain (anonymized) text of the CV.

        Returns
        -------
        CandidateData
            Pydantic model populated with data extracted from the CV.
        """
        logger.debug("Extracting CandidateData from CV text (length=%d).", len(text))
        return self._parse(
            system_prompt=_CV_SYSTEM_PROMPT,
            user_content=text,
            response_model=CandidateData,
        )

    def extract_job_offer(self, text: str) -> JobOfferData:
        """
        Extract structured requirements from a job offer text.

        Parameters
        ----------
        text:
            Plain text of the job offer.

        Returns
        -------
        JobOfferData
            Pydantic model populated with requirements extracted from the offer.
        """
        logger.debug("Extracting JobOfferData from job offer text (length=%d).", len(text))
        return self._parse(
            system_prompt=_JOB_SYSTEM_PROMPT,
            user_content=text,
            response_model=JobOfferData,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _parse(self, system_prompt: str, user_content: str, response_model: type) -> object:
        """
        Call ``client.beta.chat.completions.parse`` and return the parsed object.

        Parameters
        ----------
        system_prompt:
            Instruction context for the model.
        user_content:
            The document text to analyze.
        response_model:
            Pydantic model class used as the Structured Output schema.

        Returns
        -------
        object
            An instance of *response_model* populated by the API.

        Raises
        ------
        RuntimeError
            If the API call fails or the model refuses to produce a structured
            response (``parsed`` is ``None``).
        """
        try:
            response = self._client.beta.chat.completions.parse(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format=response_model,
            )
        except Exception as exc:
            raise RuntimeError(f"OpenAI API call failed: {exc}") from exc

        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(
                "OpenAI returned a refusal or could not produce a structured response. "
                f"Finish reason: {response.choices[0].finish_reason}"
            )

        logger.debug("Parsed %s successfully.", response_model.__name__)
        return parsed
