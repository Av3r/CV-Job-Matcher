"""
src/anonymizer.py
=================
PII-aware text anonymizer powered by Microsoft Presidio.

Design notes
------------
* ``AnalyzerEngine`` and ``AnonymizerEngine`` are constructed **once** inside
  ``__init__`` and stored as instance attributes.  Every call to
  :meth:`anonymize` and :meth:`get_detected_entities` reuses the already-loaded
  objects, so spaCy models are never reloaded per invocation.
* Language and spaCy model are configurable at construction time, defaulting to
  Polish (``pl`` / ``pl_core_news_md``) which is the model present in this
  environment.
* EMAIL_ADDRESS and PHONE_NUMBER are detected by Presidio's built-in
  regex-based recognizers (no NLP model required for them); PERSON relies on
  the spaCy NER component.
"""

from __future__ import annotations

import logging
import re
from typing import Final

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import SpacyNlpEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

#: Mapping from Presidio entity type → replacement placeholder token.
_ENTITY_PLACEHOLDER: Final[dict[str, str]] = {
    "PERSON": "[REDACTED_NAME]",
    "EMAIL_ADDRESS": "[REDACTED_EMAIL]",
    "PHONE_NUMBER": "[REDACTED_PHONE]",
    "URL": "[REDACTED_URL]",
}

#: Default list of entity types to detect and redact.
_DEFAULT_ENTITIES: Final[list[str]] = list(_ENTITY_PLACEHOLDER.keys())


# ---------------------------------------------------------------------------
# TextAnonymizer
# ---------------------------------------------------------------------------


class TextAnonymizer:
    """
    Detects and redacts personally identifiable information (PII) from text.

    Internally uses:

    * ``presidio_analyzer.AnalyzerEngine`` — identifies PII spans using a
      spaCy NLP back-end for PERSON and regex recognizers for
      EMAIL_ADDRESS / PHONE_NUMBER.
    * ``presidio_anonymizer.AnonymizerEngine`` — replaces identified spans
      with configurable placeholder tokens.

    Both engines are initialised **once** in ``__init__`` and reused for
    every call, ensuring that the (potentially heavy) spaCy model is only
    loaded a single time per ``TextAnonymizer`` instance.

    Parameters
    ----------
    language:
        BCP-47 language code passed to Presidio (e.g. ``"pl"``, ``"en"``).
        Must match the ``lang_code`` used when the spaCy model was installed.
    spacy_model:
        Name of the installed spaCy pipeline (e.g. ``"pl_core_news_md"``,
        ``"en_core_web_lg"``).  Defaults to ``"pl_core_news_md"``.
    entities:
        List of Presidio entity types to detect and redact.  Defaults to
        ``["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]``.

    Raises
    ------
    RuntimeError
        If the spaCy model cannot be loaded during initialisation (e.g. it is
        not installed in the current environment).

    Examples
    --------
    >>> anonymizer = TextAnonymizer()
    >>> anonymizer.anonymize("Contact Jan Kowalski at jan@example.com or +48 600 123 456.")
    'Contact [REDACTED_NAME] at [REDACTED_EMAIL] or [REDACTED_PHONE].'
    """

    def __init__(
        self,
        language: str = "pl",
        spacy_model: str = "pl_core_news_md",
        entities: list[str] | None = None,
    ) -> None:
        self._language = language
        self._entities: list[str] = entities if entities is not None else list(_DEFAULT_ENTITIES)

        logger.info(
            "Initializing TextAnonymizer — language=%s, spacy_model=%s, entities=%s",
            language,
            spacy_model,
            self._entities,
        )

        try:
            nlp_engine = SpacyNlpEngine(
                models=[{"lang_code": language, "model_name": spacy_model}]
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load spaCy model '{spacy_model}'. "
                f"Make sure it is installed: python -m spacy download {spacy_model}"
            ) from exc

        self._analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine,
            supported_languages=[language],
        )

        # -----------------------------------------------------------------
        # Custom regex-based recognizers
        # -----------------------------------------------------------------
        # Polish phone numbers: any 9-digit sequence split by at most one
        # non-letter character (space, dash, dot) between digit groups.
        _phone_recognizer = PatternRecognizer(
            supported_entity="PHONE_NUMBER",
            patterns=[
                Pattern(
                    name="pl_phone",
                    regex=r"\b(?:\d[\s\-\.]?){8}\d\b",
                    score=1.0,
                )
            ],
        )
        # URLs with or without scheme: linkedin.com/in/foo, https://github.com/bar
        _url_recognizer = PatternRecognizer(
            supported_entity="URL",
            patterns=[
                Pattern(
                    name="url_with_or_without_scheme",
                    regex=r"\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:/[^\s]*)?\b",
                    score=0.7,
                )
            ],
        )
        # Full name written entirely in UPPER CASE: JAN KOWALSKI
        _upper_name_recognizer = PatternRecognizer(
            supported_entity="PERSON",
            patterns=[
                Pattern(
                    name="upper_case_full_name",
                    regex=r"\b[A-Z\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b]{3,}\s+[A-Z\u0104\u0106\u0118\u0141\u0143\u00d3\u015a\u0179\u017b]{3,}\b",
                    score=1.0,
                )
            ],
        )

        registry = self._analyzer.registry
        registry.add_recognizer(_phone_recognizer)
        registry.add_recognizer(_url_recognizer)
        registry.add_recognizer(_upper_name_recognizer)

        self._anonymizer = AnonymizerEngine()

        # Build operator map once — used by every anonymize() call
        self._operators: dict[str, OperatorConfig] = {
            entity: OperatorConfig(
                "replace",
                {"new_value": _ENTITY_PLACEHOLDER.get(entity, f"[REDACTED_{entity}]")},
            )
            for entity in self._entities
        }

        logger.info("TextAnonymizer ready.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    # def anonymize(self, text: str) -> str:
    #     """
    #     Detect and redact PII entities in *text*.

    #     Detected spans are replaced in-place using the placeholder tokens
    #     defined in :data:`_ENTITY_PLACEHOLDER`.  If no PII is found the
    #     original text is returned unchanged.

    #     Parameters
    #     ----------
    #     text:
    #         Input plain text to anonymize.

    #     Returns
    #     -------
    #     str
    #         Text with all detected PII replaced by placeholder tokens.

    #     Raises
    #     ------
    #     ValueError
    #         If *text* is empty or contains only whitespace.
    #     RuntimeError
    #         If Presidio encounters an unexpected error during analysis or
    #         anonymization.
    #     """
    #     if not text or not text.strip():
    #         raise ValueError("Input text must not be empty.")

    #     # Collapse runs of spaces/tabs (≥2) to a single space so that
    #     # layout-mode whitespace from pdfplumber does not break NER and regexes.
    #     text = re.sub(r'[ \t]{2,}', ' ', text)

    #     results = self._analyze(text)

    #     if not results:
    #         logger.debug("No PII entities found — returning original text.")
    #         return text

    #     try:
    #         anonymized = self._anonymizer.anonymize(
    #             text=text,
    #             analyzer_results=results,
    #             operators=self._operators,
    #         )
    #     except Exception as exc:
    #         raise RuntimeError(f"Presidio anonymization failed: {exc}") from exc

    #     logger.debug(
    #         "Redacted %d entity/entities from text (original length=%d).",
    #         len(results),
    #         len(text),
    #     )
    #     return anonymized.text

    def anonymize(self, text: str) -> str:
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")

        # 1. Czyszczenie spacji z pdfplumber (żeby nie było "ADAM      KAMIŃSKI")
        text = re.sub(r'[ \t]{2,}', ' ', text)

        # 2. TWARDY REGEX (Brute Force) - usuwamy z tekstu przed Presidio
        # Wyłapuje imiona i nazwiska całkowicie wielkimi literami (np. ADAM KAMIŃSKI, JAN KOWALSKI)
        text = re.sub(r'\b[A-ZĄĆĘŁŃÓŚŹŻ]{3,}\s+[A-ZĄĆĘŁŃÓŚŹŻ]{3,}\b', '[REDACTED_NAME]', text)
        
        # Wyłapuje polskie formaty numerów telefonów (np. 555 333 221)
        text = re.sub(r'\b(?:\d[\s\-\.]?){8}\d\b', '[REDACTED_PHONE]', text)

        # 3. Analiza Presidio (dla e-maili i standardowych imion)
        results = self._analyze(text)

        if not results:
            logger.debug("No PII entities found — returning original text.")
            return text

        try:
            anonymized = self._anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=self._operators,
            )
        except Exception as exc:
            raise RuntimeError(f"Presidio anonymization failed: {exc}") from exc

        return anonymized.text

    def get_detected_entities(self, text: str) -> list[dict]:
        """
        Return metadata about detected PII entities without modifying the text.

        Parameters
        ----------
        text:
            Input plain text to analyze.

        Returns
        -------
        list[dict]
            Detected PII entities sorted by their character start offset.
            Each entry contains:

            * ``entity_type`` (str) — Presidio entity label.
            * ``start`` (int) — Character start offset (inclusive).
            * ``end`` (int) — Character end offset (exclusive).
            * ``score`` (float) — Confidence score in the range 0–1.
            * ``text`` (str) — The raw matched substring.

        Raises
        ------
        ValueError
            If *text* is empty or contains only whitespace.
        RuntimeError
            If analysis fails unexpectedly.
        """
        if not text or not text.strip():
            raise ValueError("Input text must not be empty.")

        results = self._analyze(text)

        return sorted(
            [
                {
                    "entity_type": r.entity_type,
                    "start": r.start,
                    "end": r.end,
                    "score": round(r.score, 4),
                    "text": text[r.start : r.end],
                }
                for r in results
            ],
            key=lambda d: d["start"],
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _analyze(self, text: str) -> list:
        """
        Run Presidio analysis on *text* and return raw ``RecognizerResult`` list.

        Centralises error handling so both :meth:`anonymize` and
        :meth:`get_detected_entities` share the same call path.

        Parameters
        ----------
        text:
            Plain text to analyze (assumed non-empty).

        Returns
        -------
        list[RecognizerResult]
            List of detected PII spans (may be empty).

        Raises
        ------
        RuntimeError
            If the underlying Presidio analyzer raises an exception.
        """
        try:
            return self._analyzer.analyze(
                text=text,
                entities=self._entities,
                language=self._language,
            )
        except Exception as exc:
            raise RuntimeError(f"Presidio analysis failed: {exc}") from exc
