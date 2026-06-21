"""Embeddings + a tiny, dependency-light vector store.

Primary backend: sentence-transformers MiniLM (real 384-dim semantic vectors,
free, local). Fallback: TF-IDF cosine (scikit-learn) when MiniLM cannot be
downloaded (offline / blocked venue wifi). Either way retrieval is genuine
vector similarity with cosine scoring, persisted to disk as a numpy matrix.

This is intentionally self-contained instead of pulling in a heavyweight vector
DB: it always runs, it is trivially explainable to a judge, and it exposes the
raw similarity score we need for the MIN_RETRIEVAL_SIM refusal gate.
"""
from __future__ import annotations

import json
import re
from typing import List, Tuple

import numpy as np

from labelguard import config

_WORD = re.compile(r"[a-z]+")


def _stem_analyze(doc: str) -> List[str]:
    """Lowercase, tokenize, and lightly stem (strip plural endings) so the
    offline TF-IDF backend matches 'vegetarians'~'vegetarian', 'claims'~'claim'."""
    out = []
    for w in _WORD.findall(doc.lower()):
        if len(w) <= 2:
            continue
        w = re.sub(r"(?:ies|es|s)$", "", w)
        out.append(w)
    return out

_BACKEND = None
_MODEL = None
_TFIDF = None


def _load_backend():
    global _BACKEND, _MODEL, _TFIDF
    if _BACKEND is not None:
        return _BACKEND
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        _MODEL = SentenceTransformer(config.EMBED_MODEL)
        _BACKEND = "minilm"
    except Exception as exc:  # offline / not installed -> TF-IDF fallback
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

        _TFIDF = TfidfVectorizer(analyzer=_stem_analyze)
        _BACKEND = "tfidf"
        print(f"[store] MiniLM unavailable ({exc.__class__.__name__}); using TF-IDF fallback.")
    return _BACKEND


def backend_name() -> str:
    return _load_backend()


def _normalize(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return m / n


class VectorStore:
    """In-memory cosine-similarity store over the clause corpus."""

    def __init__(self):
        self.ids: List[str] = []
        self.docs: List[str] = []
        self.meta: List[dict] = []
        self.mat: np.ndarray | None = None

    def build(self, clauses: List[dict]):
        backend = _load_backend()
        self.ids = [c["id"] for c in clauses]
        self.docs = [c["text"] for c in clauses]
        self.meta = clauses
        texts = [f"{c['citation']}. {c['text']}" for c in clauses]
        if backend == "minilm":
            self.mat = _normalize(np.asarray(_MODEL.encode(texts), dtype=np.float32))
        else:
            self.mat = _normalize(np.asarray(_TFIDF.fit_transform(texts).todense(), dtype=np.float32))
        return self

    def _embed_query(self, q: str) -> np.ndarray:
        if _BACKEND == "minilm":
            v = np.asarray(_MODEL.encode([q]), dtype=np.float32)
        else:
            v = np.asarray(_TFIDF.transform([q]).todense(), dtype=np.float32)
        return _normalize(v)

    def search(self, query: str, k: int = config.TOP_K, regulator: str | None = None
               ) -> List[Tuple[dict, float]]:
        """Return [(clause, cosine_sim)] top-k, optionally filtered to one regulator."""
        if self.mat is None:
            raise RuntimeError("VectorStore.build() not called")
        qv = self._embed_query(query)
        sims = (self.mat @ qv.T).ravel()
        order = np.argsort(-sims)
        out: List[Tuple[dict, float]] = []
        for idx in order:
            clause = self.meta[idx]
            if regulator and clause["regulator"] != regulator:
                continue
            out.append((clause, float(sims[idx])))
            if len(out) >= k:
                break
        return out


_STORE: VectorStore | None = None


def get_store() -> VectorStore:
    """Singleton store, built once from the corpus."""
    global _STORE
    if _STORE is None:
        from labelguard.corpus import CLAUSES

        _STORE = VectorStore().build(CLAUSES)
        print(f"[store] built {len(CLAUSES)} clauses on backend={backend_name()}")
    return _STORE
