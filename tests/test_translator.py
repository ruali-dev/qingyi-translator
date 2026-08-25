import pytest

from paper_translator.translator import (
    TranslationError,
    chat_completions_url,
    extract_chat_content,
    normalize_selection,
)


@pytest.mark.parametrize(
    ("base", "expected"),
    [
        ("https://api.openai.com/v1", "https://api.openai.com/v1/chat/completions"),
        ("https://example.test/v1/", "https://example.test/v1/chat/completions"),
        ("https://example.test/chat/completions", "https://example.test/chat/completions"),
    ],
)
def test_chat_completions_url(base: str, expected: str) -> None:
    assert chat_completions_url(base) == expected


def test_normalize_pdf_line_breaks_and_hyphenation() -> None:
    assert normalize_selection("A transla-\ntion method\nworks.") == "A translation method works."


def test_extract_chat_content_supports_string_and_parts() -> None:
    assert extract_chat_content({"choices": [{"message": {"content": "译文"}}]}) == "译文"
    assert extract_chat_content({"choices": [{"message": {"content": [{"text": "译"}, {"text": "文"}]}}]}) == "译文"


def test_extract_chat_content_rejects_missing_content() -> None:
    with pytest.raises(TranslationError):
        extract_chat_content({"choices": []})
