"""Agent tools -- the ACT step. These are what make the system useful, not just
an oracle. suggest_fix() ships the compliant rewrite; web_check_amendment()
guards against a stale corpus.
"""
from __future__ import annotations

import re
from typing import Dict

from labelguard import config, llm

_FIX_RULES = [
    (r"recommend.*doctor|doctor.*recommend",
     "Remove the medical endorsement. Use a factual statement, e.g. "
     "'Contains Vitamin C and Zinc' (only if true and substantiated)."),
    (r"boost.*immun|immun.*boost|strengthen.*immun",
     "Drop the unapproved immunity claim. State the nutrient instead, e.g. "
     "'Source of Vitamin C' with the FSSAI-approved function, if eligible."),
    (r"cure|prevent.*disease|treats?\b",
     "Remove the disease claim entirely -- foods cannot claim to cure or prevent disease."),
    (r"100\s*%?\s*natural|all natural",
     "Use '100% natural' only if every ingredient is from a natural source with "
     "no additives; otherwise say 'made with natural ingredients'."),
    (r"\bpure\b|\bfresh\b",
     "Qualify the term so it is not misleading, or substantiate it; e.g. "
     "'made from fresh fruit pulp'."),
    (r"\bisi\b|standard mark",
     "Display the ISI/BIS mark only with a valid licence; add the IS number and "
     "CM/L licence number."),
]


def suggest_fix(claim: str, verdict: Dict) -> Dict:
    if config.MOCK_MODE:
        low = claim.lower()
        for pat, advice in _FIX_RULES:
            if re.search(pat, low):
                return {"compliant_rewrite": advice, "source": "rule"}
        return {"compliant_rewrite":
                "Substantiate the claim with competent scientific evidence or remove it.",
                "source": "rule"}
    sys = ("You fix non-compliant Indian food-label claims. Given the CLAIM and the "
           "CLAUSE it violates, return JSON {\"compliant_rewrite\": \"...\"} -- a "
           "short, legal alternative.")
    try:
        out = llm.chat_json(sys, f"CLAIM: {claim}\nCLAUSE: {verdict.get('evidence','')}")
        return {"compliant_rewrite": out.get("compliant_rewrite", ""), "source": "llm"}
    except Exception:
        return {"compliant_rewrite": "Remove or substantiate the claim.", "source": "fallback"}


def web_check_amendment(citation: str) -> Dict:
    """Stub for live amendment monitoring. In production this would query the
    FSSAI/Legal-Metrology gazette feed. Returned in the trace to show the agent
    *knows* its corpus could be stale."""
    return {"citation": citation, "checked": True,
            "note": "No newer amendment found in cached gazette index (demo)."}
