"""Per-cell table + exact tests for PREREG_INSITU. Usage: python3 analyze_insitu.py runs_insitu/"""
import json, glob, sys, os, collections
from math import comb
root = sys.argv[1] if len(sys.argv) > 1 else "runs_insitu"
cells = collections.defaultdict(list)
for f in glob.glob(f"{root}/rep*/*/*/verified_eval.json"):
    rep, task, cond = f.split("/")[-4:-1]
    cells[(task, cond)].append(bool(json.load(open(f)).get("useful")))
def fisher_one_sided(a, b, c, d):  # P(X >= a) for [[a,b],[c,d]]
    n = a + b + c + d; r1 = a + b; c1 = a + c
    return sum(comb(r1, x) * comb(n - r1, c1 - x) for x in range(a, min(r1, c1) + 1)) / comb(n, c1)
print(f"{'task':6s}{'cond':9s}{'useful/k'}")
tot = collections.defaultdict(lambda: [0, 0])
for task in ("T_A", "T_B", "T_C"):
    for cond in ("NoKB", "NegOnly", "NegCal"):
        v = cells.get((task, cond), []); print(f"{task:6s}{cond:9s}{sum(v)}/{len(v)}")
        tot[cond][0] += sum(v); tot[cond][1] += len(v)
print("pooled:", {c: f"{u}/{k}" for c, (u, k) in tot.items()})
u1, k1 = tot["NegCal"]; u0, k0 = tot["NegOnly"]
if k1 and k0:
    print(f"H1 NegCal>NegOnly one-sided Fisher p = {fisher_one_sided(u1, k1-u1, u0, k0-u0):.4f}")
