"""
tests/test_anonymizer.py
========================
Unit tests for TextAnonymizer.

All tests mock the Presidio engines so the heavy spaCy model is never
loaded during the test run (fast, no model required in CI).

Run with:
    pytest tests/test_anonymizer.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# We patch the heavy objects before importing the module under test
from src.anonymizer import TextAnonymizer, _DEFAULT_ENTITIES, _ENTITY_PLACEHOLDER


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_recognizer_result(entity_type: str, start: int, end: int, score: float = 0.85):
    """Return a lightweight mock that mimics presidio RecognizerResult."""
    r = MagicMock()
    r.entity_type = entity_type
    r.start = start
    r.end = end
    r.score = score
    return r


def _make_anonymizer_result(text: str):
    """Return a mock that mimics presidio AnonymizedText."""
    result = MagicMock()
    result.text = text
    return result


# ---------------------------------------------------------------------------
# Fixture: TextAnonymizer with all presidio internals mocked
# ---------------------------------------------------------------------------


@pytest.fixture()
def anonymizer():
    """
    Return a TextAnonymizer whose heavy presidio/spaCy objects are replaced
    with mocks.  This prevents the spaCy model from being loaded during tests.
    """
    with (
        patch("src.anonymizer.SpacyNlpEngine") as mock_nlp,
        patch("src.anonymizer.AnalyzerEngine") as mock_analyzer_cls,
        patch("src.anonymizer.AnonymizerEngine") as mock_anon_cls,
    ):
        mock_nlp.return_value = MagicMock()
        mock_analyzer_cls.return_value = MagicMock()
        mock_anon_cls.return_value = MagicMock()
        ta = TextAnonymizer(language="pl", spacy_model="pl_core_news_md")
    return ta


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestInitialization:
    def test_default_entities_are_set(self, anonymizer: TextAnonymizer) -> None:
        assert anonymizer._entities == _DEFAULT_ENTITIES

    def test_custom_entities_are_stored(self) -> None:
        with (
            patch("src.anonymizer.SpacyNlpEngine"),
            patch("src.anonymizer.AnalyzerEngine"),
            patch("src.anonymizer.AnonymizerEngine"),
        ):
            ta = TextAnonymizer(entities=["PERSON"])
        assert ta._entities == ["PERSON"]

    def test_operators_created_for_each_entity(self, anonymizer: TextAnonymizer) -> None:
        for entity in anonymizer._entities:
            assert entity in anonymizer._operators

    def test_placeholder_values_match_constants(self, anonymizer: TextAnonymizer) -> None:
        for entity, op_config in anonymizer._operators.items():
            expected = _ENTITY_PLACEHOLDER.get(entity, f"[REDACTED_{entity}]")
            assert op_config.params["new_value"] == expected

    def test_unknown_entity_gets_generic_placeholder(self) -> None:
        with (
            patch("src.anonymizer.SpacyNlpEngine"),
            patch("src.anonymizer.AnalyzerEngine"),
            patch("src.anonymizer.AnonymizerEngine"),
        ):
            ta = TextAnonymizer(entities=["LOCATION"])
        assert ta._operators["LOCATION"].params["new_value"] == "[REDACTED_LOCATION]"

    def test_spacy_load_failure_raises_runtime_error(self) -> None:
        with (
            patch("src.anonymizer.SpacyNlpEngine", side_effect=OSError("model not found")),
            pytest.raises(RuntimeError, match="Failed to load spaCy model"),
        ):
            TextAnonymizer()


# ---------------------------------------------------------------------------
# anonymize()
# ---------------------------------------------------------------------------


class TestAnonymize:
    def test_raises_value_error_on_empty_string(self, anonymizer: TextAnonymizer) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            anonymizer.anonymize("")

    def test_raises_value_error_on_whitespace_only(self, anonymizer: TextAnonymizer) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            anonymizer.anonymize("   ")

    def test_returns_original_text_when_no_pii_detected(
        self, anonymizer: TextAnonymizer
    ) -> None:
        anonymizer._analyzer.analyze.return_value = []
        result = anonymizer.anonymize("Hello, world!")
        assert result == "Hello, world!"

    def test_person_is_redacted(self, anonymizer: TextAnonymizer) -> None:
        results = [_make_recognizer_result("PERSON", 8, 20)]
        anonymizer._analyzer.analyze.return_value = results
        anonymizer._anonymizer.anonymize.return_value = _make_anonymizer_result(
            "Contact [REDACTED_NAME] for details."
        )
        output = anonymizer.anonymize("Contact Jan Kowalski for details.")
        assert "[REDACTED_NAME]" in output
        assert "Jan Kowalski" not in output

    def test_email_is_redacted(self, anonymizer: TextAnonymizer) -> None:
        results = [_make_recognizer_result("EMAIL_ADDRESS", 6, 24)]
        anonymizer._analyzer.analyze.return_value = results
        anonymizer._anonymizer.anonymize.return_value = _make_anonymizer_result(
            "Mail: [REDACTED_EMAIL]"
        )
        output = anonymizer.anonymize("Mail: jan@example.com")
        assert "[REDACTED_EMAIL]" in output

    def test_phone_is_redacted(self, anonymizer: TextAnonymizer) -> None:
        results = [_make_recognizer_result("PHONE_NUMBER", 7, 23)]
        anonymizer._analyzer.analyze.return_value = results
        anonymizer._anonymizer.anonymize.return_value = _make_anonymizer_result(
            "Phone: [REDACTED_PHONE]"
        )
        output = anonymizer.anonymize("Phone: +48 600 123 456")
        assert "[REDACTED_PHONE]" in output

    def test_multiple_entities_redacted_in_one_call(self, anonymizer: TextAnonymizer) -> None:
        results = [
            _make_recognizer_result("PERSON", 0, 12),
            _make_recognizer_result("EMAIL_ADDRESS", 16, 34),
        ]
        anonymizer._analyzer.analyze.return_value = results
        anonymizer._anonymizer.anonymize.return_value = _make_anonymizer_result(
            "[REDACTED_NAME] — [REDACTED_EMAIL]"
        )
        output = anonymizer.anonymize("Jan Kowalski — jan@example.com")
        assert "[REDACTED_NAME]" in output
        assert "[REDACTED_EMAIL]" in output

    def test_analyzer_is_called_with_correct_args(self, anonymizer: TextAnonymizer) -> None:
        anonymizer._analyzer.analyze.return_value = []
        anonymizer.anonymize("Some plain text.")
        anonymizer._analyzer.analyze.assert_called_once_with(
            text="Some plain text.",
            entities=anonymizer._entities,
            language=anonymizer._language,
        )

    def test_anonymizer_engine_not_called_when_no_results(
        self, anonymizer: TextAnonymizer
    ) -> None:
        anonymizer._analyzer.analyze.return_value = []
        anonymizer.anonymize("No PII here.")
        anonymizer._anonymizer.anonymize.assert_not_called()

    def test_runtime_error_on_analyzer_failure(self, anonymizer: TextAnonymizer) -> None:
        anonymizer._analyzer.analyze.side_effect = Exception("NLP crash")
        with pytest.raises(RuntimeError, match="Presidio analysis failed"):
            anonymizer.anonymize("Some text.")

    def test_runtime_error_on_anonymizer_failure(self, anonymizer: TextAnonymizer) -> None:
        anonymizer._analyzer.analyze.return_value = [
            _make_recognizer_result("PERSON", 0, 5)
        ]
        anonymizer._anonymizer.anonymize.side_effect = Exception("engine crash")
        with pytest.raises(RuntimeError, match="Presidio anonymization failed"):
            anonymizer.anonymize("Alice works here.")


# ---------------------------------------------------------------------------
# get_detected_entities()
# ---------------------------------------------------------------------------


class TestGetDetectedEntities:
    def test_raises_value_error_on_empty_string(self, anonymizer: TextAnonymizer) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            anonymizer.get_detected_entities("")

    def test_returns_empty_list_when_nothing_detected(
        self, anonymizer: TextAnonymizer
    ) -> None:
        anonymizer._analyzer.analyze.return_value = []
        result = anonymizer.get_detected_entities("No PII here.")
        assert result == []

    def test_result_structure_contains_required_keys(
        self, anonymizer: TextAnonymizer
    ) -> None:
        anonymizer._analyzer.analyze.return_value = [
            _make_recognizer_result("EMAIL_ADDRESS", 5, 23)
        ]
        text = "Mail jan@example.com end"
        result = anonymizer.get_detected_entities(text)
        assert len(result) == 1
        entry = result[0]
        assert set(entry.keys()) == {"entity_type", "start", "end", "score", "text"}

    def test_result_text_slice_matches_source(self, anonymizer: TextAnonymizer) -> None:
        text = "Email: jan@example.com done"
        anonymizer._analyzer.analyze.return_value = [
            _make_recognizer_result("EMAIL_ADDRESS", 7, 22)
        ]
        result = anonymizer.get_detected_entities(text)
        assert result[0]["text"] == text[7:22]

    def test_results_sorted_by_start_offset(self, anonymizer: TextAnonymizer) -> None:
        anonymizer._analyzer.analyze.return_value = [
            _make_recognizer_result("EMAIL_ADDRESS", 30, 48),
            _make_recognizer_result("PERSON", 0, 12),
        ]
        text = "Jan Kowalski writes jan@example.com daily"
        result = anonymizer.get_detected_entities(text)
        assert result[0]["start"] < result[1]["start"]

    def test_score_is_rounded_to_4_decimal_places(
        self, anonymizer: TextAnonymizer
    ) -> None:
        anonymizer._analyzer.analyze.return_value = [
            _make_recognizer_result("PERSON", 0, 5, score=0.851234567)
        ]
        result = anonymizer.get_detected_entities("Alice was here.")
        assert result[0]["score"] == round(0.851234567, 4)

    def test_runtime_error_on_analyzer_failure(self, anonymizer: TextAnonymizer) -> None:
        anonymizer._analyzer.analyze.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError, match="Presidio analysis failed"):
            anonymizer.get_detected_entities("Some text.")


# ---------------------------------------------------------------------------
# Model reuse — engines not re-constructed on repeated calls
# ---------------------------------------------------------------------------


class TestModelReuse:
    def test_analyzer_instance_is_reused_across_calls(
        self, anonymizer: TextAnonymizer
    ) -> None:
        """The same AnalyzerEngine object must be used for every call."""
        anonymizer._analyzer.analyze.return_value = []
        first_ref = anonymizer._analyzer
        anonymizer.anonymize("First call.")
        anonymizer.anonymize("Second call.")
        assert anonymizer._analyzer is first_ref

    def test_anonymizer_instance_is_reused_across_calls(
        self, anonymizer: TextAnonymizer
    ) -> None:
        """AnonymizerEngine object must be the same instance across multiple calls."""
        anonymizer._analyzer.analyze.return_value = []
        first_ref = anonymizer._anonymizer
        anonymizer.anonymize("First call.")
        anonymizer.anonymize("Second call.")
        assert anonymizer._anonymizer is first_ref
