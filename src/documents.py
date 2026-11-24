"""Loading course documents and eval cases from disk."""

import re
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = ROOT / "data" / "documents"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def load_document(relative_path: str) -> str:
    """Read a saved document (txt, md, html or pdf) from data/documents/ as plain text."""
    path = DOCUMENTS_DIR / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Document not found: {path}")
    suffix = path.suffix.lower()
    if suffix in (".txt", ".md"):
        return path.read_text(encoding="utf-8")
    if suffix in (".html", ".htm"):
        extractor = _TextExtractor()
        extractor.feed(path.read_text(encoding="utf-8", errors="replace"))
        return re.sub(r"[ \t]+", " ", "\n".join(extractor.parts))
    if suffix == ".pdf":
        if not shutil.which("pdftotext"):
            raise RuntimeError("pdftotext is needed to read PDFs but was not found on PATH.")
        result = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=True,
        )
        return result.stdout
    raise ValueError(f"Unsupported document type: {path.suffix}")


def load_case(case_id: str) -> dict:
    """Load one case from eval/cases.csv (the single place where cases are defined)."""
    from .cases import load_case as _load_case

    return _load_case(case_id)
