"""The agentic loop. This is the orchestrator -- the part that *decides*.

For each claim:
    route -> retrieve (regulator-filtered) -> judge -> verify (MoV) -> gate -> act

Gates, all enforced in CODE (not prompts):
  * Refusal:        no relevant clause -> NOT_COVERED, confidence 0.
  * Re-retrieve:    faithfulness < gate -> retrieve once more (broader), re-judge.
  * Critic overturn: LogicExpert finds a counter-clause -> flip COMPLIANT down.
  * Confidence floor: verdict < CONFIDENCE_FLOOR -> NEEDS_HUMAN_REVIEW.

Every step is recorded in a `trace` so the UI can show the agent thinking and a
judge can audit exactly how a verdict was reached.
"""
from __future__ import annotations

import re
import time
from typing import Dict, List

from labelguard import config, extract, judge as judger, router, verifiers
from labelguard.store import get_store
from labelguard.tools import suggest_fix


def _retrieve(claim: str, regulator: str | None, k: int):
    return get_store().search(claim, k=k, regulator=regulator)


def audit_claim(claim: str) -> Dict:
    t0 = time.time()
    trace: List[str] = []

    # 1) ROUTE -----------------------------------------------------------
    r = router.route(claim)
    regulator = r["regulator"]
    trace.append(f"ROUTE -> {regulator} ({r['reason']})")

    # 2) RETRIEVE (regulator-filtered) -----------------------------------
    clauses = _retrieve(claim, regulator, config.TOP_K)
    top_sim = clauses[0][1] if clauses else 0.0
    trace.append(f"RETRIEVE {regulator}: top={clauses[0][0]['id'] if clauses else None} "
                 f"sim={top_sim:.2f}")

    # Refusal gate: corpus has nothing relevant -> refuse, do not guess
    if not clauses or top_sim < config.MIN_RETRIEVAL_SIM:
        trace.append("REFUSE: no relevant clause (sim below floor)")
        return _finalize(claim, regulator, {
            "verdict": "NOT_COVERED", "confidence": 0, "evidence_id": None,
            "evidence": "", "citation": "", "regulator": regulator,
            "rationale": "No relevant clause; system refuses to judge.",
            "retrieval_sim": round(top_sim, 3)},
            [], None, trace, t0)

    # 3) JUDGE -----------------------------------------------------------
    verdict = judger.judge(claim, clauses)
    trace.append(f"JUDGE -> {verdict['verdict']} ({verdict['confidence']}%) "
                 f"cite={verdict['evidence_id']}")

    # Terminal refusal: judge could not ground a verdict -> do not downgrade,
    # do not re-loop. Refusing is a valid, final answer.
    if verdict["verdict"] == "NOT_COVERED":
        trace.append("REFUSE: judge found no decisive clause")
        checks = [verifiers.source_matcher(verdict, clauses)]
        return _finalize(claim, regulator, verdict, checks, None, trace, t0)

    # 4) VERIFY (Mixture-of-Verifiers) -----------------------------------
    checks = verifiers.run_all(claim, verdict, clauses)
    hh = next(c for c in checks if c["name"] == "HallucinationHunter")

    # Re-retrieve once if ungrounded
    if not hh["passed"]:
        trace.append(f"HallucinationHunter FAIL ({hh['score']}); re-retrieving broader")
        clauses = _retrieve(claim, None, config.TOP_K + 2)  # drop regulator filter
        verdict = judger.judge(claim, clauses)
        checks = verifiers.run_all(claim, verdict, clauses)
        hh = next(c for c in checks if c["name"] == "HallucinationHunter")
        if not hh["passed"]:
            verdict["verdict"] = "NEEDS_HUMAN_REVIEW"
            trace.append("Still ungrounded -> NEEDS_HUMAN_REVIEW")

    # Critic overturn
    le = next(c for c in checks if c["name"] == "LogicExpert")
    if le.get("overturn"):
        trace.append(f"LogicExpert OVERTURN via {le.get('counter_id')}")
        verdict["verdict"] = "NON_COMPLIANT"
        verdict["confidence"] = max(verdict["confidence"], 80)
        verdict["evidence_id"] = le["counter_id"]
        verdict["evidence"] = le["counter_text"]
        verdict["citation"] = le["counter_citation"]
        verdict["rationale"] = f"Overturned by critic: {le['counter_citation']}."

    # 5) ACT: suggest a compliant rewrite for failing claims --------------
    fix = None
    if verdict["verdict"] in ("NON_COMPLIANT", "NEEDS_SUBSTANTIATION"):
        fix = suggest_fix(claim, verdict)
        trace.append("ACT -> suggested compliant rewrite")

    return _finalize(claim, regulator, verdict, checks, fix, trace, t0)


def _finalize(claim, regulator, verdict, checks, fix, trace, t0) -> Dict:
    # Confidence floor (code-enforced)
    if verdict["verdict"] not in ("NOT_COVERED",) and verdict.get("confidence", 0) < config.CONFIDENCE_FLOOR:
        verdict["verdict"] = "NEEDS_HUMAN_REVIEW"
        trace.append(f"Confidence {verdict.get('confidence')}% < floor -> NEEDS_HUMAN_REVIEW")
    if verdict["verdict"] not in config.VALID_VERDICTS:
        verdict["verdict"] = "NOT_COVERED"
    faith = next((c["score"] for c in (checks or []) if c["name"] == "HallucinationHunter"), 0.0)
    return {
        "claim": claim,
        "regulator": regulator,
        "verdict": verdict["verdict"],
        "confidence": verdict.get("confidence", 0),
        "faithfulness": faith,
        "evidence_id": verdict.get("evidence_id"),
        "evidence": verdict.get("evidence", ""),
        "citation": verdict.get("citation", ""),
        "rationale": verdict.get("rationale", ""),
        "checks": checks or [],
        "fix": fix,
        "trace": trace,
        "latency_s": round(time.time() - t0, 3),
    }


def audit_label(*, text: str | None = None, image: bytes | None = None,
                pdf: bytes | None = None) -> Dict:
    """Top-level entry: extract claims from any input, audit each, aggregate."""
    claims = extract.extract(text=text, image=image, pdf=pdf)
    results = [audit_claim(c) for c in claims]
    counts: Dict[str, int] = {}
    for r in results:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    risk = "HIGH" if counts.get("NON_COMPLIANT") else (
        "MEDIUM" if counts.get("NEEDS_SUBSTANTIATION") or counts.get("NEEDS_HUMAN_REVIEW")
        else "LOW")
    return {
        "claims_found": len(claims),
        "results": results,
        "summary": counts,
        "overall_risk": risk,
        "disclaimer": config.DISCLAIMER,
    }
