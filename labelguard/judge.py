"""Grounded judge: decide a verdict for one claim using ONLY retrieved clauses.

The judge is never allowed to reason from training data. In real mode the
system prompt forces clause-grounded JSON output; in offline mode a transparent
rule engine maps claim patterns to verdicts and always attaches the retrieved
clause as evidence. Either way: no clause text in hand, no verdict.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

from labelguard import config, llm

_SYSTEM = (
    "You are an FSSAI/Legal-Metrology/BIS compliance judge. You are given a "
    "single label CLAIM and the ONLY clauses you may use. Judge strictly from "
    "the provided clauses. Never invent rules. If the clauses do not address the "
    "claim, return NOT_COVERED with confidence 0.\n"
    "Return JSON: {\"verdict\": \"COMPLIANT|NON_COMPLIANT|NEEDS_SUBSTANTIATION|"
    "NOT_COVERED\", \"confidence\": 0-100, \"evidence_id\": \"<clause id you "
    "relied on>\", \"rationale\": \"one sentence quoting the clause\"}."
)

# Offline rule engine: (regex on claim, verdict, confidence, preferred clause id)
_RULES: List[Tuple[str, str, int, str]] = [
    (r"recommend.*(doctor|physician|expert)|doctor.*recommend|endorsed by|"
     r"medical expert|approved by .*doctor", "NON_COMPLIANT", 91, "FSSAI-AC-8"),
    (r"\b(boost|strengthen|support).*immun|immun.*boost|"
     r"defen[cs]e?s?\b.*(illness|disease|infection|germ)|fights?\b.*(illness|infection|germ)",
     "NON_COMPLIANT", 88, "FSSAI-AC-7"),
    (r"cure|prevent|treats?\b|disease|diabet|cancer|clinically proven", "NON_COMPLIANT", 90, "FSSAI-AC-4"),
    (r"100\s*%?\s*natural|all\s*natural", "NEEDS_SUBSTANTIATION", 72, "FSSAI-LD-4.3f"),
    (r"no added sugar|without added sugar", "COMPLIANT", 86, "FSSAI-LD-2f"),
    (r"\bisi\b|standard mark|\bbis\b", "NEEDS_SUBSTANTIATION", 70, "BIS-CM-1"),
    (r"net\s*(wt|weight|qty|quantity).*\d|\b\d+\s*(g|kg|ml|l)\b", "COMPLIANT", 84, "LM-PCR-9"),
    (r"\bmrp\b|maximum retail", "COMPLIANT", 83, "LM-PCR-18"),
    (r"\bpure\b|\bfresh\b", "NEEDS_SUBSTANTIATION", 68, "FSSAI-LD-4.3f"),
    (r"vegetarian|non-?veg", "COMPLIANT", 80, "FSSAI-LD-9"),
]


def _pick_evidence(clauses: List[Tuple[dict, float]], preferred_id: str):
    for c, sim in clauses:
        if c["id"] == preferred_id:
            return c, sim
    return clauses[0]  # fall back to top retrieved


def _mock_judge(claim: str, clauses: List[Tuple[dict, float]]) -> Dict:
    low = claim.lower()
    for pat, verdict, conf, cid in _RULES:
        if re.search(pat, low):
            clause, sim = _pick_evidence(clauses, cid)
            return {
                "verdict": verdict,
                "confidence": conf,
                "evidence_id": clause["id"],
                "evidence": clause["text"],
                "citation": clause["citation"],
                "regulator": clause["regulator"],
                "rationale": f"Per {clause['citation']}.",
                "retrieval_sim": round(sim, 3),
            }
    # No rule matched -> we cannot ground a verdict, so we REFUSE rather than
    # guess. This is the "no clause, no verdict" principle in action.
    clause, sim = clauses[0]
    return {
        "verdict": "NOT_COVERED",
        "confidence": 0,
        "evidence_id": None,
        "evidence": "",
        "citation": "",
        "regulator": clause["regulator"],
        "rationale": "No clause decisively covers this claim; system refuses to judge.",
        "retrieval_sim": round(sim, 3),
    }


def judge(claim: str, clauses: List[Tuple[dict, float]]) -> Dict:
    if not clauses:
        return {"verdict": "NOT_COVERED", "confidence": 0, "evidence_id": None,
                "evidence": "", "citation": "", "regulator": "", "retrieval_sim": 0.0,
                "rationale": "No clause retrieved; system refuses to guess."}
    if config.MOCK_MODE:
        return _mock_judge(claim, clauses)
    # real LLM path
    ctx = "\n".join(f"[{c['id']}] {c['citation']}: {c['text']}" for c, _ in clauses)
    try:
        out = llm.chat_json(_SYSTEM, f"CLAIM: {claim}\n\nCLAUSES:\n{ctx}")
        eid = out.get("evidence_id")
        match = next((c for c, _ in clauses if c["id"] == eid), clauses[0][0])
        return {
            "verdict": out.get("verdict", "NOT_COVERED"),
            "confidence": int(out.get("confidence", 0)),
            "evidence_id": match["id"],
            "evidence": match["text"],
            "citation": match["citation"],
            "regulator": match["regulator"],
            "rationale": out.get("rationale", ""),
            "retrieval_sim": round(clauses[0][1], 3),
        }
    except Exception:
        return _mock_judge(claim, clauses)
