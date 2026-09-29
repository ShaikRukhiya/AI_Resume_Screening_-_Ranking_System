from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from pypdf import PdfReader


def read_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return "\n".join(pages)


def read_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            return ""
        xml_data = archive.read("word/document.xml")
        root = ET.fromstring(xml_data)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = root.findall(".//w:t", ns)
        text_parts = [node.text or "" for node in paragraphs]
        return " ".join(text_parts)


def read_txt_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def extract_text_from_file(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return read_pdf_text(path)
    if suffix == ".docx":
        return read_docx_text(path)
    if suffix == ".txt":
        return read_txt_text(path)
    raise ValueError(f"Unsupported file format: {suffix}")
