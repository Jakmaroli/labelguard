"""Multimodal claim extraction: image / PDF / raw text -> list of claims.

This is the upgrade that kills the "wrapper" objection: a real user drops in
the actual packaging artwork, not typed text.

Pipeline:
  image bytes -> vision LLM reads the label -> claims          (real mode)
              -> OCR (pytesseract) -> text -> claim splitter    (fallback)
  pdf bytes   -> PyMuPDF text -> claim splitter
  raw text    -> claim splitter

A "claim" is any marketing/regulatory assertion on the label worth auditing.
"""
from __future__ import annotations

import io
import re
from typing import List

from labelguard import config, llm

_VISION_PROMPT = (
    "You are reading a food/FMCG product label image. List every distinct "
    "marketing or regulatory CLAIM printed on it (health claims, ingredient "
    "claims, net quantity, MRP, certification marks, endorsements). Return "
    "JSON: {\"claims\": [\"...\", \"...\"]}. One short claim per item, verbatim "
    "where possible."
)

# Phrases that signal a regulated assertion -- used by the offline splitter.
_SIGNAL = [
    "immunity", "immune", "boost", "doctor", "recommended", "no added sugar",
    "sugar free", "natural", "100%", "pure", "fresh", "net wt", "net weight",
    "net qty", "mrp", "maximum retail", "isi", "bis", "certified", "vegetarian",
    "non-veg", "fssai", "lic. no", "licence", "organic", "clinically", "cures",
    "prevents", "weight loss", "ml", "litre", "kg", "grams", "g)",
]


def _split_claims(text: str) -> List[str]:
    """Offline splitter: break label text into candidate claims."""
    text = re.sub(r"\s+", " ", text).strip()
    # split on common label separators
    parts = re.split(r"[\n\.;|•·]| - |, (?=[A-Z])", text)
    claims: List[str] = []
    for p in parts:
        p = p.strip(" -·•\t")
        if len(p) < 3:
            continue
        low = p.lower()
        if any(s in low for s in _SIGNAL) or len(p.split()) <= 8:
            claims.append(p)
    # de-dup, keep order
    seen, out = set(), []
    for c in claims:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out[:12]


def from_text(text: str) -> List[str]:
    return _split_claims(text)


def from_pdf(data: bytes) -> List[str]:
    import fitz  # PyMuPDF

    doc = fitz.open(stream=data, filetype="pdf")
    text = "\n".join(page.get_text() for page in doc)
    return _split_claims(text)


def from_image(data: bytes) -> List[str]:
    """Vision LLM in real mode; OCR fallback offline."""
    if not config.MOCK_MODE:
        try:
            raw = llm.vision_extract(data, _VISION_PROMPT)
            obj = llm.parse_json(raw)
            claims = [c.strip() for c in obj.get("claims", []) if c.strip()]
            if claims:
                return claims[:12]
        except Exception as exc:
            print(f"[extract] vision failed ({exc}); falling back to OCR.")
    # OCR fallback
    try:
        import pytesseract  # type: ignore
        from PIL import Image

        text = pytesseract.image_to_string(Image.open(io.BytesIO(data)))
        if text.strip():
            return _split_claims(text)
    except Exception as exc:
        print(f"[extract] OCR unavailable ({exc}).")
    return []


def extract(*, text: str | None = None, image: bytes | None = None,
            pdf: bytes | None = None) -> List[str]:
    if text:
        return from_text(text)
    if pdf:
        return from_pdf(pdf)
    if image:
        return from_image(image)
    return []
