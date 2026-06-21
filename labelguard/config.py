"""Central configuration for LabelGuard Pro.

Everything is tunable from here. The most important switch is MOCK_MODE:
if no GROQ_API_KEY is present we fall back to a deterministic, rule-based
"LLM" so the entire system runs offline with zero credentials. This means
your live demo never dies on hackathon-venue wifi.
"""
from __future__ import annotations

import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STORE_DIR = ROOT / ".vectorstore"
STORE_DIR.mkdir(exist_ok=True)

# --- LLM -------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
TEXT_MODEL = os.getenv("LG_TEXT_MODEL", "llama-3.3-70b-versatile")
VISION_MODEL = os.getenv("LG_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
# MOCK_MODE = no API calls. Auto-on when no key. Force with LG_MOCK=1.
MOCK_MODE = (not GROQ_API_KEY) or os.getenv("LG_MOCK", "") == "1"

# --- Retrieval -------------------------------------------------------------
TOP_K = 4                      # clauses retrieved per claim
EMBED_MODEL = "all-MiniLM-L6-v2"

# --- Decision thresholds (enforced in CODE, never left to the LLM) ---------
CONFIDENCE_FLOOR = 50          # below this -> NEEDS_HUMAN_REVIEW
FAITHFULNESS_GATE = 0.70       # below this -> re-retrieve once, then downgrade
MIN_RETRIEVAL_SIM = 0.05       # hard floor: near-zero overlap -> refuse (judge rules handle the rest)
CRITIC_SIM = 0.40              # LogicExpert only overturns on a strong counter-clause

VALID_VERDICTS = {
    "COMPLIANT",
    "NON_COMPLIANT",
    "NEEDS_SUBSTANTIATION",
    "NOT_COVERED",
    "NEEDS_HUMAN_REVIEW",
}

REGULATORS = {
    "FSSAI": "Food Safety & Standards Authority of India (claims, health, labelling)",
    "LEGAL_METROLOGY": "Legal Metrology (Packaged Commodities) Rules 2011 (quantity, MRP, origin)",
    "BIS": "Bureau of Indian Standards (ISI mark, standard marks, certification)",
}

DISCLAIMER = (
    "LabelGuard Pro is a pre-launch advisory tool, not a legal authority or "
    "enforcement mechanism. Final compliance sign-off must come from a qualified "
    "professional. Ungroundable claims are escalated for human review, never guessed."
)
