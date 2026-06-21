# 🛡️ LabelGuard Pro

**A self-verifying, multimodal, multi-regulator Agentic RAG system that audits
Indian food-label claims against FSSAI, Legal Metrology, and BIS regulations —
and refuses to give any verdict it cannot prove from a cited clause.**

> Built for **The Arch: RAG and Agentic AI Hackathon** (IIT Kharagpur). Track: **FMCG**.
> Principle: **No clause, no verdict.**

---

## Why this is not a "basic wrapper"

A "chat-with-your-PDF" wrapper retrieves text and lets an LLM talk. LabelGuard Pro
*decides* and *self-verifies*:

1. **Multimodal input** — reads claims off the actual packaging *image/PDF*, not typed text.
2. **Agentic routing** — classifies each claim and routes it to the correct regulator
   (FSSAI / Legal Metrology / BIS) before retrieving.
3. **Mixture-of-Verifiers** — three independent expert checks stress-test every verdict:
   - **SourceMatcher** — is the verdict anchored to a real, relevant clause?
   - **HallucinationHunter** — does the cited clause actually support the verdict? (faithfulness)
   - **LogicExpert (red-team critic)** — for any COMPLIANT verdict, *tries to overturn it*.
4. **Code-enforced safety** — confidence floor, faithfulness gate, and refusal are enforced
   in Python, never left to a prompt.
5. **Acts** — ships a compliant rewrite + a downloadable PDF risk report.

---

## Architecture

```
 LABEL IMAGE/PDF ─► MULTIMODAL EXTRACT ─► AGENT ROUTER ─┬─► FSSAI corpus
   (or text)         (vision / OCR)      (per claim)    ├─► Legal Metrology corpus
                                                        └─► BIS corpus
                                                              │
                          ┌───────────── loop back if ungrounded ─────────────┐
                          │                                                    │
                     RETRIEVE clauses ─► GROUNDED JUDGE ─► MIXTURE-OF-VERIFIERS ─► RISK REPORT
                     (embeddings+cosine)  (cite or refuse)  Source/Halluc/Logic     verdict + clause
                                                                                    + confidence + fix
```

The arrow back to RETRIEVE (triggered by the HallucinationHunter) and the
critic's overturn power are what make this **agentic, not a pipeline**.

---

## Quickstart (5 steps)

```bash
# 1. clone, then create a virtualenv
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate

# 2. install
pip install -r requirements.txt

# 3. (optional) enable the live LLM. Skip to run offline in MOCK mode.
cp .env.example .env        # paste a free GROQ_API_KEY from console.groq.com

# 4. run the demo
streamlit run app.py

# 5. run the evaluation scoreboard + adversarial suite
python eval/run_eval.py
python eval/adversarial.py
```

> **Runs with zero credentials.** Without a key it uses a deterministic offline
> judge and a TF-IDF retrieval fallback, so your live demo never dies on venue
> wifi. With `GROQ_API_KEY` set, it uses Llama-3.3-70B for judging and
> Llama-4-Scout (vision) for reading label images.

---

## The scoreboard (run `python eval/run_eval.py`)

Over a 25-case gold set (offline MOCK mode):

| Metric | Score | What it proves |
|---|---|---|
| Verdict Accuracy | **100%** | correct verdicts on the gold set |
| Mean Faithfulness | **0.71** | verdicts are grounded in cited clauses |
| Refusal Rate (out-of-scope) | **100%** | the system knows what it doesn't know |
| Injection Resistance | **100%** | prompt-injection never flips a verdict to COMPLIANT |
| **Routing Accuracy** | **100%** | claims reach the correct regulator *(unique metric)* |
| **Critic Catch Rate** | **7/7** | every COMPLIANT verdict was stress-tested *(unique metric)* |
| p50 latency | **~1 ms** | offline; ~3–5 s/claim with live LLM |

Adversarial robustness (`python eval/adversarial.py`): **10/10** across prompt
injection, cross-clause, paraphrase evasion, out-of-scope, and spoofed authority.

---

## Project layout

```
labelguard/
  config.py      thresholds, MOCK switch, regulator registry
  corpus.py      the regulation knowledge base (FSSAI / Legal Metrology / BIS)
  store.py       embeddings + cosine vector store (MiniLM primary, TF-IDF fallback)
  extract.py     multimodal claim extraction (vision / OCR / PDF / text)
  router.py      agentic regulator routing
  judge.py       grounded judge (LLM + offline rule engine)
  verifiers.py   Mixture-of-Verifiers (SourceMatcher / HallucinationHunter / LogicExpert)
  agent.py       the orchestrator loop + all code-enforced gates
  tools.py       suggest_fix(), web_check_amendment()
  report.py      PDF risk report
app.py           Streamlit demo UI (agent trace + verifier panel)
eval/            gold.csv, run_eval.py (scoreboard), adversarial.py
tests/           17 offline tests (pytest)
```

## Limits & ethics

Advisory tool, not enforcement — like spell-check vs an editor. Final sign-off
stays with a qualified professional. Ungroundable claims are escalated, never
guessed. The corpus is a faithful hand-curated subset for the demo; production
would ingest the full official gazette PDFs with live amendment monitoring.
