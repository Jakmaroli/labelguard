"""LabelGuard Pro -- Streamlit demo UI.

Run:  streamlit run app.py
Works with zero credentials (offline MOCK mode). Add GROQ_API_KEY to .env to
enable the live LLM judge + vision label reading.
"""
from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from labelguard import config  # noqa: E402
from labelguard.agent import audit_label  # noqa: E402
from labelguard.report import to_pdf  # noqa: E402
from labelguard.store import backend_name  # noqa: E402

st.set_page_config(page_title="LabelGuard Pro", page_icon="🛡️", layout="wide")

_BADGE = {
    "COMPLIANT": ("#1a7f37", "✅"), "NON_COMPLIANT": ("#c1121f", "⛔"),
    "NEEDS_SUBSTANTIATION": ("#b06a00", "⚠️"), "NEEDS_HUMAN_REVIEW": ("#6a4cff", "🧑‍⚖️"),
    "NOT_COVERED": ("#555", "🚫"),
}
_RISK = {"HIGH": "#c1121f", "MEDIUM": "#b06a00", "LOW": "#1a7f37"}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("🛡️ LabelGuard Pro")
    st.caption("Self-verifying · multimodal · multi-regulator Agentic RAG")
    mode = "🟢 LIVE (Groq LLM)" if not config.MOCK_MODE else "🟠 OFFLINE (mock judge)"
    st.metric("Mode", mode)
    st.metric("Retrieval backend", backend_name())
    st.divider()
    st.subheader("Regulators covered")
    for k, v in config.REGULATORS.items():
        st.markdown(f"**{k}** — {v}")
    st.divider()
    st.markdown("**Principle:** _No clause, no verdict._")

# ---------------------------------------------------------------- header
st.title("🛡️ LabelGuard Pro")
st.markdown(
    "Drop in a **product-label image / PDF** or paste label copy. The agent "
    "**routes** each claim to the right regulator, **retrieves** the governing "
    "clause, **judges** strictly from it, then a **Mixture-of-Verifiers** "
    "(Source Matcher · Hallucination Hunter · Logic-Expert critic) stress-tests "
    "every verdict. Ungroundable claims are **refused**, not guessed."
)

tab_text, tab_file = st.tabs(["📝 Paste label text", "🖼️ Upload label image / PDF"])
text_input = None
file_bytes = None
file_kind = None

with tab_text:
    text_input = st.text_area(
        "Label / ad copy",
        "VitaGlow Health Drink. Boosts immunity. Recommended by leading doctors. "
        "No added sugar. 100% natural. Net wt 500 g. MRP Rs 199 inclusive of all taxes.",
        height=130,
    )
with tab_file:
    up = st.file_uploader("Label artwork (PNG/JPG) or PDF", type=["png", "jpg", "jpeg", "pdf"])
    if up:
        file_bytes = up.read()
        file_kind = "pdf" if up.name.lower().endswith("pdf") else "image"
        if file_kind == "image":
            st.image(file_bytes, caption="Uploaded label", width=320)

run = st.button("🔍 Audit label", type="primary", use_container_width=True)


def verdict_chip(v):
    color, icon = _BADGE.get(v, ("#000", ""))
    return (f"<span style='background:{color};color:#fff;padding:3px 10px;"
            f"border-radius:12px;font-weight:600;font-size:0.85rem'>{icon} {v}</span>")


if run:
    with st.spinner("Routing → retrieving → judging → verifying…"):
        if file_bytes and file_kind == "image":
            report = audit_label(image=file_bytes)
        elif file_bytes and file_kind == "pdf":
            report = audit_label(pdf=file_bytes)
        else:
            report = audit_label(text=text_input)

    rc = _RISK.get(report["overall_risk"], "#555")
    st.markdown(
        f"<div style='padding:14px;border-radius:10px;background:{rc}1a;"
        f"border:1px solid {rc}'><b>Overall risk: "
        f"<span style='color:{rc}'>{report['overall_risk']}</span></b> &nbsp;·&nbsp; "
        f"{report['claims_found']} claims audited &nbsp;·&nbsp; {report['summary']}</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    for i, r in enumerate(report["results"], 1):
        with st.container(border=True):
            c1, c2, c3 = st.columns([6, 2, 2])
            with c1:
                st.markdown(f"**Claim {i}:** “{r['claim']}”")
                st.markdown(verdict_chip(r["verdict"]) +
                            f" &nbsp; <span style='color:#888'>[{r['regulator']}]</span>",
                            unsafe_allow_html=True)
            c2.metric("Confidence", f"{r['confidence']}%")
            c3.metric("Faithfulness", f"{r['faithfulness']:.2f}")

            if r.get("citation"):
                st.markdown(f"📎 **Cited clause [{r['evidence_id']}]** — *{r['citation']}*")
                st.caption(r["evidence"])
            if r.get("rationale"):
                st.markdown(f"🧠 {r['rationale']}")
            if r.get("fix"):
                st.success(f"✅ Compliant rewrite: {r['fix']['compliant_rewrite']}")

            # Mixture-of-Verifiers
            vc = st.columns(len(r["checks"]))
            for col, chk in zip(vc, r["checks"]):
                mark = "✅" if chk["passed"] else "❌"
                col.markdown(f"{mark} **{chk['name']}**  \n`{chk['score']}`  \n"
                             f"<span style='font-size:0.75rem;color:#888'>{chk['note']}</span>",
                             unsafe_allow_html=True)

            with st.expander("🔬 Agent trace (how this verdict was reached)"):
                for step in r["trace"]:
                    st.code(step, language=None)

    st.divider()
    pdf = to_pdf(report)
    st.download_button("⬇️ Download PDF risk report", pdf,
                       file_name="labelguard_report.pdf", mime="application/pdf")
    st.caption(report["disclaimer"])
