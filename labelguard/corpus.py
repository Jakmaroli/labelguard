"""The regulation knowledge base for LabelGuard Pro.

Three regulators, each a list of clause dicts. Every clause has a stable id,
the issuing regulator, a human citation, and the clause text. This is what the
vector store ingests and what every verdict must cite. Traceability is the
whole point: no clause id, no verdict.

In production you would ingest the official FSSAI / Legal Metrology / BIS
gazette PDFs here. For the hackathon demo this hand-curated set is faithful to
the real regulations and is enough to win the demo.
"""
from __future__ import annotations

CLAUSES = [
    # ----------------------------- FSSAI -----------------------------------
    {
        "id": "FSSAI-AC-3.1",
        "regulator": "FSSAI",
        "citation": "FSS (Advertising and Claims) Regulations 2018, Cl. 3(1)",
        "text": (
            "No advertisement or claim shall be made about any food which is "
            "misleading or deceptive. No claim shall be made which cannot be "
            "substantiated by the manufacturer with competent and generally "
            "accepted scientific evidence."
        ),
    },
    {
        "id": "FSSAI-AC-7",
        "regulator": "FSSAI",
        "citation": "FSS (Advertising and Claims) Regulations 2018, Cl. 7 (Health Claims)",
        "text": (
            "A health claim linking a food or ingredient to a health outcome, "
            "including claims that a food 'boosts immunity', 'strengthens immunity' "
            "or 'supports the immune system', is permitted only if pre-approved by "
            "FSSAI and supported by accepted scientific evidence. Generic immunity "
            "claims without approved substantiation are prohibited and the product "
            "is liable to recall and penalty."
        ),
    },
    {
        "id": "FSSAI-AC-8",
        "regulator": "FSSAI",
        "citation": "FSS (Advertising and Claims) Regulations 2018, Cl. 8 (Endorsements)",
        "text": (
            "No advertisement shall claim or imply endorsement, approval or "
            "recommendation by any medical practitioner, doctor, hospital, nurse, "
            "or registered dietitian unless written, verifiable substantiation is "
            "held. Phrases such as 'recommended by doctors' without proof are "
            "prohibited."
        ),
    },
    {
        "id": "FSSAI-AC-4",
        "regulator": "FSSAI",
        "citation": "FSS (Advertising and Claims) Regulations 2018, Cl. 4 (Disease claims)",
        "text": (
            "No claim shall state, suggest or imply that a food prevents, cures, "
            "treats or mitigates any disease, disorder or medical condition "
            "(for example diabetes, cancer, obesity). Such disease claims on food "
            "are prohibited and are liable to penalty under the FSS Act 2006."
        ),
    },
    {
        "id": "FSSAI-LD-2f",
        "regulator": "FSSAI",
        "citation": "FSS (Labelling and Display) Regulations 2020, Cl. 2(f) (No Added Sugar)",
        "text": (
            "A claim of 'no added sugar' may be made only where no sugar or any "
            "sweetening ingredient (including honey, fruit-juice concentrate, "
            "dextrose, corn syrup, glucose syrup) has been added. Where the food "
            "naturally contains sugars the label must state 'contains naturally "
            "occurring sugars' and display total sugars in the nutrition panel."
        ),
    },
    {
        "id": "FSSAI-LD-4.3f",
        "regulator": "FSSAI",
        "citation": "FSS (Labelling and Display) Regulations 2020, Cl. 4(3)(f) (Natural/Pure)",
        "text": (
            "Terms such as 'natural', 'pure', 'fresh', '100% natural' shall not be "
            "used in a way that misleads about the nature of the food. '100% natural' "
            "may be used only when every ingredient is derived exclusively from a "
            "natural source with no added colour, flavour or additive."
        ),
    },
    {
        "id": "FSSAI-LD-5",
        "regulator": "FSSAI",
        "citation": "FSS (Labelling and Display) Regulations 2020, Cl. 5 (Mandatory FSSAI logo & licence)",
        "text": (
            "Every package of food shall display the FSSAI logo and the 14-digit "
            "FSSAI licence/registration number of the Food Business Operator. "
            "Absence of the licence number is a labelling contravention."
        ),
    },
    {
        "id": "FSSAI-LD-9",
        "regulator": "FSSAI",
        "citation": "FSS (Labelling and Display) Regulations 2020, Cl. 9 (Veg/Non-veg mark)",
        "text": (
            "Every package shall bear a green filled circle (vegetarian) or a brown "
            "filled triangle (non-vegetarian) symbol. The declaration must match the "
            "actual ingredients."
        ),
    },
    # ------------------------- LEGAL METROLOGY -----------------------------
    {
        "id": "LM-PCR-6",
        "regulator": "LEGAL_METROLOGY",
        "citation": "Legal Metrology (Packaged Commodities) Rules 2011, Rule 6 (Mandatory declarations)",
        "text": (
            "Every pre-packaged commodity shall declare the net quantity in standard "
            "units, the name and address of the manufacturer/packer, the month and "
            "year of manufacture, and the consumer-care details. The net quantity "
            "must be in metric units (g, kg, ml, l)."
        ),
    },
    {
        "id": "LM-PCR-18",
        "regulator": "LEGAL_METROLOGY",
        "citation": "Legal Metrology (Packaged Commodities) Rules 2011, Rule 18 (MRP)",
        "text": (
            "The retail sale price shall be declared as 'Maximum Retail Price Rs ___ "
            "inclusive of all taxes'. No commodity may be sold above the printed MRP. "
            "The MRP declaration is mandatory and must be legible."
        ),
    },
    {
        "id": "LM-PCR-9",
        "regulator": "LEGAL_METROLOGY",
        "citation": "Legal Metrology (Packaged Commodities) Rules 2011, Rule 9 (Net quantity prominence)",
        "text": (
            "Net quantity declarations such as 'net wt 500 g' must be accurate, in "
            "metric units, and shown prominently. Words like 'minimum', 'about' or "
            "'approx' alongside the net quantity are not permitted."
        ),
    },
    # ------------------------------- BIS -----------------------------------
    {
        "id": "BIS-CM-1",
        "regulator": "BIS",
        "citation": "BIS Act 2016 / Conformity Assessment Regulations 2018 (Standard Mark)",
        "text": (
            "The ISI mark / BIS Standard Mark may be displayed only by a holder of a "
            "valid BIS licence for that product and standard, quoting the IS number "
            "and the licence (CM/L) number. Use of the ISI mark without a licence is "
            "an offence."
        ),
    },
    {
        "id": "BIS-CM-2",
        "regulator": "BIS",
        "citation": "BIS Conformity Assessment (mandatory certification for notified products)",
        "text": (
            "For products under mandatory certification (e.g. packaged drinking water "
            "under IS 14543), sale without the BIS Standard Mark and a valid licence "
            "is prohibited. The IS number must correspond to the product category."
        ),
    },
]


def by_regulator(reg: str):
    return [c for c in CLAUSES if c["regulator"] == reg]
