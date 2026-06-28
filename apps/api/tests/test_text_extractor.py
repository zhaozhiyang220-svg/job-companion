from pathlib import Path

import pytest

from src.services.text_extractor import extract_text

FIX = Path(__file__).parent / "fixtures"


def test_extract_docx() -> None:
    data = (FIX / "sample.docx").read_bytes()
    text = extract_text("sample.docx", data)
    assert "张三" in text
    assert "PM" in text


def test_extract_pdf() -> None:
    data = (FIX / "sample.pdf").read_bytes()
    text = extract_text("sample.pdf", data)
    assert "Zhang San" in text


def test_unsupported_extension_raises() -> None:
    with pytest.raises(ValueError):
        extract_text("resume.txt", b"hello")
