"""Risk report rendering: a downloadable PDF audit trail. Real-world utility =
the brand manager walks away with a document, not a chat log.
"""
from __future__ import annotations

import io
from typing import Dict

_BADGE = {
    "COMPLIANT": "#1a7f37", "NON_COMPLIANT": "#c1121f",
    "NEEDS_SUBSTANTIATION": "#b06a00", "NEEDS_HUMAN_REVIEW": "#6a4cff",
    "NOT_COVERED": "#555555",
}


def to_pdf(report: Dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    HRFlowable)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, title="LabelGuard Pro Risk Report")
    styles = getSampleStyleSheet()
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor="#555")
    flow = [
        Paragraph("LabelGuard Pro — Compliance Risk Report", styles["Title"]),
        Paragraph(f"Overall risk: <b>{report['overall_risk']}</b> &nbsp; "
                  f"Claims audited: {report['claims_found']} &nbsp; "
                  f"Summary: {report['summary']}", styles["Normal"]),
        Spacer(1, 8), HRFlowable(width="100%"), Spacer(1, 8),
    ]

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))

    for i, r in enumerate(report["results"], 1):
        color = _BADGE.get(r["verdict"], "#000")
        flow.append(Paragraph(f"<b>Claim {i}:</b> “{esc(r['claim'])}”  "
                              f"<font color='#888'>[{esc(r['regulator'])}]</font>",
                              styles["Heading4"]))
        flow.append(Paragraph(
            f"Verdict: <b><font color='{color}'>{esc(r['verdict'])}</font></b> &nbsp; "
            f"confidence {r['confidence']}% &nbsp; faithfulness {r['faithfulness']}",
            styles["Normal"]))
        if r.get("citation"):
            flow.append(Paragraph(f"<i>Clause [{esc(r['evidence_id'])}] "
                                  f"{esc(r['citation'])}:</i> {esc(r['evidence'])}", small))
        if r.get("fix"):
            flow.append(Paragraph(f"✅ Fix: {esc(r['fix'].get('compliant_rewrite',''))}",
                                  styles["Normal"]))
        flow.append(Spacer(1, 6))

    flow += [HRFlowable(width="100%"), Spacer(1, 4),
             Paragraph(esc(report["disclaimer"]), small)]
    doc.build(flow)
    return buf.getvalue()
