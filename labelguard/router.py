"""Agentic router: classify each claim and route it to the right regulator.

This is what makes the system *decide* rather than run a fixed pipeline. A net
quantity claim must be judged against Legal Metrology, an ISI mark against BIS,
a health claim against FSSAI. Routing to the wrong corpus = wrong verdict, so
this step is scored in the eval (Routing Accuracy).

Real mode uses the LLM; offline mode uses a transparent keyword classifier.
Both return one of config.REGULATORS keys (or "FSSAI" as the safe default,
since most label claims are FSSAI-governed).
"""
from __future__ import annotations

import re
from typing import Dict

from labelguard import config, llm

_RULES = [
    ("LEGAL_METROLOGY", [
        r"net\s*(wt|weight|qty|quantity)", r"\bmrp\b", r"maximum retail",
        r"\b\d+\s*(g|kg|ml|l|litre|gram)s?\b", r"manufactured (on|by)",
        r"month.*year", r"\bquantity\b", r"inclusive of all taxes",
    ]),
    ("BIS", [
        r"\bisi\b", r"\bbis\b", r"standard mark", r"\bIS\s*\d+", r"cm/l",
        r"certified to is", r"packaged drinking water",
    ]),
    ("FSSAI", [
        r"immun", r"doctor", r"recommend", r"no added sugar", r"sugar free",
        r"natural", r"100%", r"\bpure\b", r"\bfresh\b", r"health", r"boost",
        r"vegetarian", r"non-?veg", r"fssai", r"organic", r"clinically",
        r"cure", r"prevent", r"disease",
    ]),
]

_SYSTEM = (
    "You route a single food-label claim to the correct Indian regulator. "
    "Reply JSON: {\"regulator\": \"FSSAI|LEGAL_METROLOGY|BIS\", \"reason\": \"...\"}. "
    "FSSAI = health/ingredient/marketing claims, endorsements, label terms. "
    "LEGAL_METROLOGY = net quantity, MRP, manufacturer/packer details, dates. "
    "BIS = ISI mark, standard marks, IS numbers, mandatory certification."
)


def _rule_route(claim: str) -> Dict:
    low = claim.lower()
    for reg, pats in _RULES:
        for p in pats:
            if re.search(p, low):
                return {"regulator": reg, "reason": f"matched pattern '{p}'"}
    return {"regulator": "FSSAI", "reason": "default: general marketing claim"}


def route(claim: str) -> Dict:
    if config.MOCK_MODE:
        return _rule_route(claim)
    try:
        out = llm.chat_json(_SYSTEM, f"Claim: {claim}")
        reg = out.get("regulator", "FSSAI")
        if reg not in config.REGULATORS:
            reg = "FSSAI"
        return {"regulator": reg, "reason": out.get("reason", "")}
    except Exception:
        return _rule_route(claim)
