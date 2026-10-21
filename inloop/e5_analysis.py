"""E5 analysis: enforced-lock LLM cell vs the soft-deference E4 cell.
Usage: python3 e5_analysis.py   (from this dir, after running the E5 cells; expects the E4 files present too)
Decision rules are preregistered in PREREG_E5.md — this script only computes them."""
import json, glob, os
import numpy as np
from itertools import combinations

R = "results"
BASETAG = None
for f in glob.glob(f"{R}/llm_loop_*_hard_gated_enf.json"):
    BASETAG = os.path.basename(f)[len("llm_loop_"):-len("_enf.json")]
if BASETAG is None:
    exit("no _enf loop file found — run the E5 cells first")

def effs_of(loopfile):
    J = json.load(open(loopfile))
    return J, {k: (J["BM"] - v) / J["SIG"] for k, v in J["truth"].items()}

Jse, Ese = effs_of(f"{R}/llm_loop_{BASETAG}.json")        # E4 soft
Jen, Een = effs_of(f"{R}/llm_loop_{BASETAG}_enf.json")    # E5 enforced

def load_events(tag):
    ev = {}
    f = f"{R}/llm_events_{tag}.jsonl"
    if os.path.exists(f):
        for ln in open(f):
            r = json.loads(ln); ev.setdefault((r["cond"], r["rep"]), []).append(r)
    return ev

def discoveries(tag, effs, cond, events=None):
    out = []
    for f in sorted(glob.glob(f"{R}/llm_state_{tag}_{cond}_*.json")):
        st = json.load(open(f))
        rep = int(f.rsplit("_", 1)[1].split(".")[0])
        conf = set(st["confirmed"])
        d = sum(effs.get(c, -9) > 0 for c in conf)
        wr = sum(1 for k in st["records"] if effs.get(k, -9) > 0 and k not in conf)
        seq = (events or {}).get((cond, rep))
        if seq:  # STRICT rescue: first 'record' precedes 'confirm' (paper's definition); also audit train-while-locked
            order = {}
            for s in seq:
                order.setdefault(s["key"], []).append(s["event"])
            resc = sum(1 for k, evs in order.items()
                       if "confirm" in evs and "record" in evs
                       and evs.index("record") < evs.index("confirm") and effs.get(k, -9) > 0)
            leaks = sum(1 for s in seq if s["event"] == "train" and s.get("locked_at_train"))
        else:    # fallback: loose set intersection (order-blind; may include confirm-then-record quirk cases)
            resc = sum(1 for k in st["records"] if k in conf and effs.get(k, -9) > 0)
            leaks = -1
        # NOTE: in soft cells, "leaks" = trainings of would-be-locked configs = the behavioral retry count (a feature);
        # in enforced cells it must be 0 (an actual enforcement leak otherwise).
        out.append(dict(disc=d, wrongful=wr, rescued=resc, leaks=leaks,
                        blocks=st.get("enforce_blocks", 0), forfeits=st.get("enforce_forfeits", 0),
                        gate=st.get("gate_rejects", 0), distinct=len(set(st["proposals"]))))
    return out

def mw_p(a, b):
    """exact one-sided rank p for a > b"""
    U = sum(x > y for x in a for y in b)
    pool = list(a) + list(b); n = len(a); ge = tot = 0
    for idx in combinations(range(len(pool)), n):
        aa = [pool[i] for i in idx]; bb = [pool[i] for i in range(len(pool)) if i not in idx]
        tot += 1; ge += (sum(x > y for x in aa for y in bb) >= U)
    return ge / tot

cells = {}
for name, tag, effs in (("soft", BASETAG, Ese), ("enforced", f"{BASETAG}_enf", Een)):
    events = load_events(tag)
    for cond in ("binary", "graded"):
        rows = discoveries(tag, effs, cond, events)
        if rows: cells[(name, cond)] = rows

print(f"{'cell':22s}{'disc (per rep)':22s}{'mean±sd':12s}{'wrongful':9s}{'rescued':8s}{'blocks':7s}{'forfeits':8s}{'retrained-locked':16s}")
for (name, cond), rows in cells.items():
    ds = [r["disc"] for r in rows]
    print(f"{name+'/'+cond:22s}{str(ds):22s}{np.mean(ds):5.1f}±{np.std(ds, ddof=1):4.1f}  "
          f"{sum(r['wrongful'] for r in rows):<9d}{sum(r['rescued'] for r in rows):<8d}"
          f"{sum(r['blocks'] for r in rows):<7d}{sum(r['forfeits'] for r in rows):<8d}"
          f"{sum(max(r['leaks'],0) for r in rows):<16d}")

if ("enforced", "binary") in cells and ("enforced", "graded") in cells:
    gb = [r["disc"] for r in cells[("enforced", "graded")]]
    bb = [r["disc"] for r in cells[("enforced", "binary")]]
    p = mw_p(gb, bb)
    print(f"\nH1 primary: enforced graded vs enforced binary — point estimates "
          f"{np.mean(gb):.1f} vs {np.mean(bb):.1f}, exact one-sided rank p={p:.4f}")
    resc_b = sum(r["rescued"] for r in cells[("enforced", "binary")])
    leaks_b = sum(max(r["leaks"], 0) for r in cells[("enforced", "binary")] + cells[("enforced", "graded")])
    print(f"H1 causal signature: STRICT rescues under enforced binary = {resc_b} (must be 0); "
          f"train-while-locked events across enforced cells = {leaks_b} (must be 0)")
    if ("soft", "binary") in cells:
        sb = [r["disc"] for r in cells[("soft", "binary")]]
        print(f"H1 secondary: enforced binary {np.mean(bb):.1f} vs soft binary {np.mean(sb):.1f} "
              f"(one-sided soft>enforced p={mw_p(sb, bb):.4f})")
    if ("soft", "graded") in cells:
        sg = [r["disc"] for r in cells[("soft", "graded")]]
        print(f"context: enforced graded {np.mean(gb):.1f} vs soft graded {np.mean(sg):.1f}")
    verdict = "H1-direction" if np.mean(gb) > np.mean(bb) else "H2-direction"
    strength = "resolved" if p <= 0.2 else "underpowered (report as directional only — per PREREG_E5.md)"
    print(f"\nPreregistered read: {verdict}, {strength}")
