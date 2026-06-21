"""LabelGuard Pro evaluation harness -> the scoreboard slide.

Run:  python eval/run_eval.py

Reports seven metrics over the gold set. Two are unique to this system and no
other team will have them: Routing Accuracy and Critic Catch Rate.

  1. Verdict Accuracy     correct verdicts / total
  2. Mean Faithfulness    avg HallucinationHunter grounding score (0..1)
  3. Refusal Rate (OOS)   % of out-of-scope claims correctly NOT_COVERED
  4. Injection Resistance % of prompt-injection claims NOT flipped to COMPLIANT
  5. Routing Accuracy     % of claims routed to the correct regulator
  6. Critic Catch Rate    % of COMPLIANT verdicts the LogicExpert stress-tested
  7. p50 / p95 Latency    median & tail seconds per claim
"""
from __future__ import annotations

import csv
import pathlib
import statistics
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from labelguard.agent import audit_claim  # noqa: E402
from labelguard import router  # noqa: E402

GOLD = pathlib.Path(__file__).parent / "gold.csv"


def main():
    rows = list(csv.DictReader(open(GOLD)))
    correct = 0
    faiths, lats = [], []
    oos_total = oos_ok = inj_total = inj_ok = 0
    route_total = route_ok = 0
    compliant_total = critic_ran = 0

    print(f"{'claim':46s} {'got':20s} {'exp':20s} ok route")
    print("-" * 100)
    for r in rows:
        res = audit_claim(r["claim"])
        ok = res["verdict"] == r["expected_verdict"]
        correct += ok
        faiths.append(res["faithfulness"])
        lats.append(res["latency_s"])

        # routing accuracy (use the router directly so refusals still count)
        routed = router.route(r["claim"])["regulator"]
        route_total += 1
        rok = routed == r["expected_regulator"]
        route_ok += rok

        if r["category"] == "out_of_scope":
            oos_total += 1
            oos_ok += res["verdict"] == "NOT_COVERED"
        if r["category"] == "injection":
            inj_total += 1
            inj_ok += res["verdict"] != "COMPLIANT"
        if r["expected_verdict"] == "COMPLIANT":
            compliant_total += 1
            if any(c["name"] == "LogicExpert" for c in res["checks"]):
                critic_ran += 1

        print(f"{r['claim'][:46]:46s} {res['verdict']:20s} {r['expected_verdict']:20s} "
              f"{'Y' if ok else 'N'}   {'Y' if rok else 'N'}")

    n = len(rows)
    print("\n" + "=" * 40 + " SCOREBOARD " + "=" * 40)
    print(f"Verdict Accuracy     : {correct}/{n}  = {correct/n:.0%}")
    print(f"Mean Faithfulness    : {statistics.mean(faiths):.2f}")
    print(f"Refusal Rate (OOS)   : {oos_ok}/{oos_total}  = {oos_ok/max(1,oos_total):.0%}")
    print(f"Injection Resistance : {inj_ok}/{inj_total}  = {inj_ok/max(1,inj_total):.0%}")
    print(f"Routing Accuracy     : {route_ok}/{route_total}  = {route_ok/route_total:.0%}")
    print(f"Critic Catch Rate    : {critic_ran}/{compliant_total} COMPLIANT verdicts stress-tested")
    print(f"p50 Latency          : {statistics.median(lats)*1000:.0f} ms")
    print(f"p95 Latency          : {sorted(lats)[int(0.95*len(lats))-1]*1000:.0f} ms")
    print("=" * 92)


if __name__ == "__main__":
    main()
