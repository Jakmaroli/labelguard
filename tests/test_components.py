"""Unit tests for router, verifiers, store, and report."""
import os
import pathlib
import sys

os.environ["LG_MOCK"] = "1"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from labelguard import router, verifiers, report  # noqa: E402
from labelguard.store import get_store  # noqa: E402
from labelguard.agent import audit_label  # noqa: E402


def test_router_quantity_to_legal_metrology():
    assert router.route("Net weight 250 g")["regulator"] == "LEGAL_METROLOGY"


def test_router_default_is_fssai():
    assert router.route("Tastes great")["regulator"] == "FSSAI"


def test_store_retrieval_returns_scored_clauses():
    hits = get_store().search("boosts immunity", k=3, regulator="FSSAI")
    assert len(hits) == 3
    assert all(0.0 <= sim <= 1.0001 for _, sim in hits)


def test_logic_expert_only_challenges_compliant():
    verdict = {"verdict": "NON_COMPLIANT", "evidence_id": "X", "confidence": 90}
    out = verifiers.logic_expert("anything", verdict)
    assert out["overturn"] is False


def test_source_matcher_fails_without_clause():
    verdict = {"verdict": "NOT_COVERED", "evidence_id": None, "retrieval_sim": 0.0}
    out = verifiers.source_matcher(verdict, [])
    assert out["passed"] is False


def test_pdf_report_is_generated():
    rep = audit_label(text="Boosts immunity. No added sugar.")
    pdf = report.to_pdf(rep)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000
