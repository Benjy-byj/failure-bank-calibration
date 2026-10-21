"""LLM-in-the-loop closed-loop experiment (closed-loop headline).
A real LLM (deepseek-chat) proposes hyperparameter configs; every verdict is a real
sklearn MLP training run; the failure bank is presented IN THE PROMPT and never
enforced in code -- deference is behavioral, exactly as deployed. Four memory
conditions differ only in what the bank shows:
  nomem   : no bank shown
  binary  : failed configs listed as "Status: DEAD"
  graded  : failed configs listed with evidence + P(dead); prompt says only
            records with P(dead)>0.8 are considered closed
  parole  : DEAD list, but prompt notes ~5% of closed records are re-opened for review
Measured: truth-validated discoveries per budget AND the true-effect distribution
of every distinct LLM-proposed config (the marginal-abundance measurement).
Resumable per (condition, rep): state checkpoints + run cache + API log.
Usage:  export DEEPSEEK_API_KEY=...   then   python llm_loop.py [budget] [reps]
"""
import json, os, sys, time, math, warnings, urllib.request
warnings.filterwarnings("ignore")
import numpy as np
from sklearn.datasets import load_digits
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss

import argparse
_ap = argparse.ArgumentParser()
_ap.add_argument("budget", nargs="?", type=int, default=150)
_ap.add_argument("reps", nargs="?", type=int, default=3)
_ap.add_argument("--provider", default="deepseek", choices=["deepseek", "openrouter"])
_ap.add_argument("--model", default=None)
_ap.add_argument("--reasoning-tokens", type=int, default=0, help="cap for reasoning models via openrouter; 0 = off")
_ap.add_argument("--hard", action="store_true", help="strong baseline: remaining gains are scarce/marginal (phase-boundary cell)")
_ap.add_argument("--gated", action="store_true", help="success-gated supply: proposals must be one-step neighbors of confirmed configs (or baseline)")
_ap.add_argument("--par", type=int, default=1, help="run this many replicate loops concurrently (threads; cache/logs lock-protected)")
_ap.add_argument("--enforce", action="store_true", help="E5: code-level lock enforcement — proposals of DEAD/CLOSED configs are blocked before running (no budget cost, re-prompt, 3-strike slot forfeit); mirrors the algorithmic loop's structural lock")
_A = _ap.parse_args()
BUDGET, REPS = _A.budget, _A.reps
_PROV = {"deepseek": ("https://api.deepseek.com/v1/chat/completions", "DEEPSEEK_API_KEY", "deepseek-chat"),
         "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY", "openai/gpt-4o")}
API, _ENV, _DEF = _PROV[_A.provider]
MODEL = _A.model or _DEF
KEY = os.environ.get(_ENV) or exit(f"export {_ENV} first")
TAG = f"{_A.provider}_{MODEL.replace('/', '-')}" + ("_hard" if _A.hard else "") + ("_gated" if _A.gated else "") + ("_enf" if _A.enforce else "")
ENFORCE = _A.enforce
GATED = _A.gated
CONDS = ["nomem", "binary", "graded"] if GATED else ["nomem", "binary", "graded", "parole"]
if ENFORCE:
    CONDS = ["binary", "graded"]  # E5: enforcement is undefined for nomem; parole out of scope

X, y = load_digits(return_X_y=True)
rs = np.random.RandomState(1234); idx = rs.permutation(len(X))
tr, va = idx[:1200], idx[1200:]
sc = StandardScaler().fit(X[tr])
Xtr, Xva, ytr, yva = sc.transform(X[tr]), sc.transform(X[va]), y[tr], y[va]

GRID = {"lr": [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2],
        "hidden": [8, 16, 32, 64, 128, 256],
        "alpha": [1e-6, 1e-5, 1e-4, 1e-3, 1e-2, 1e-1],
        "batch": [32, 64, 128, 256],
        "act": ["relu", "tanh", "logistic"],
        "b1": [0.85, 0.9, 0.95]}
BASE = {"lr": 1e-3, "hidden": 32, "alpha": 1e-4, "batch": 64, "act": "relu", "b1": 0.9}
if _A.hard:
    BASE = {"lr": 3e-3, "hidden": 128, "alpha": 1e-4, "batch": 128, "act": "relu", "b1": 0.9}
ITER = 40
os.makedirs("results", exist_ok=True)

import threading
_LOCK = threading.Lock()
cache = {}
CF = "results/llm_cache.jsonl"
if os.path.exists(CF):
    for ln in open(CF):
        r = json.loads(ln); cache[(json.dumps(r["cfg"], sort_keys=True), r["seed"])] = r["loss"]

def train(cfg, seed):
    k = (json.dumps(cfg, sort_keys=True), seed)
    with _LOCK:
        if k in cache: return cache[k]
    m = MLPClassifier(hidden_layer_sizes=(cfg["hidden"],), learning_rate_init=cfg["lr"],
                      alpha=cfg["alpha"], batch_size=cfg["batch"], activation=cfg["act"],
                      beta_1=cfg["b1"], solver="adam", max_iter=ITER, tol=0.0, random_state=seed)
    m.fit(Xtr, ytr)
    loss = float(log_loss(yva, m.predict_proba(Xva), labels=np.unique(y)))
    with _LOCK:
        cache[k] = loss
        with open(CF, "a") as f: f.write(json.dumps({"cfg": cfg, "seed": seed, "loss": loss}) + "\n")
    return loss

base_runs = [train(BASE, 10_000 + i) for i in range(12)]
BM, SIG = float(np.mean(base_runs)), float(np.std(base_runs, ddof=1))
GRID_TXT = "\n".join(f"- {k}: one of {v}" for k, v in GRID.items())

def pdead_of(ev):
    n = len(ev); mean_d = np.mean(ev) - BM
    return 1 - 0.5 * (1 + math.erf(-(mean_d / (SIG / math.sqrt(n))) / math.sqrt(2)))

def locked_keys(cond, records, parole_open):
    """keys the enforcement layer blocks: binary/parole = every record (minus paroled), graded = CLOSED only"""
    if cond == "nomem": return set()
    if cond == "graded":
        return {k for k, ev in records.items() if pdead_of(ev) > 0.8}
    return set(records) - set(parole_open or [])

def bank_text(cond, records, parole_note):
    if cond == "nomem" or not records: return ""
    lines = []
    for key, ev in records.items():
        cfg = json.loads(key)
        short = ", ".join(f"{k}={cfg[k]}" for k in GRID)
        if cond == "binary" or cond == "parole":
            lines.append(f"- [{short}] Status: DEAD.")
        else:  # graded
            n = len(ev); mean_d = np.mean(ev) - BM
            pdead = pdead_of(ev)
            status = "CLOSED" if pdead > 0.8 else "OPEN (weak evidence)"
            lines.append(f"- [{short}] {n} run(s), mean {'+' if mean_d>=0 else ''}{mean_d:.4f} vs baseline, P(dead)={pdead:.2f}. Status: {status}.")
    head = "Shared failure bank (verdicts from earlier sessions):"
    if cond == "graded":
        head += "\nOnly records with P(dead)>0.8 are considered closed; OPEN records may be re-proposed."
    if cond == "parole" and parole_note:
        head += "\nNote: this session, the following previously-closed records have been re-opened for review: " + parole_note
    return head + "\n" + "\n".join(lines[-40:])

def propose(cond, confirmed, records, parole_note, tried_recent, blocked_note=""):
    if os.environ.get("LLM_STUB"):
        return _stub_propose(cond, confirmed, records)
    conf_txt = "\n".join(f"- {', '.join(f'{k}={json.loads(c)[k]}' for k in GRID)} (confirmed better)"
                         for c in confirmed[-15:]) or "(none yet)"
    prompt = f"""You are the experiment-proposal module of an autonomous hyperparameter-search agent.
Task: minimize validation log-loss of an MLP on a digits dataset. Baseline config {BASE} has loss {BM:.4f} (seed-to-seed std {SIG:.4f}). Each experiment costs one training run from a fixed budget.
Search space (pick each value from its list):
{GRID_TXT}
Confirmed improvements so far:
{conf_txt}
{bank_text(cond, records, parole_note)}
Recently proposed this session (avoid exact repeats unless you have a reason): {tried_recent[-8:]}
Budget is consumed by every run: re-proposing a config that is already confirmed, or one you have already tried this session, wastes a slot. Prefer untried configs.
{"Supply rule (strict): propose ONLY configs that differ from the baseline or from one of your confirmed configs in exactly ONE parameter by one grid step. Anything else is discarded unscored and the slot is lost." if GATED else ""}
{"Enforcement (strict): the system blocks any proposal whose bank status is DEAD or CLOSED --- it is rejected before it can run and you will be asked to propose a different config." if ENFORCE else ""}{blocked_note}
Propose the single most promising next config. Answer with ONLY a JSON object, no prose:
{{"lr": ..., "hidden": ..., "alpha": ..., "batch": ..., "act": "...", "b1": ...}}"""
    _b = {"model": MODEL, "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]}
    if _A.reasoning_tokens: _b["reasoning"] = {"max_tokens": _A.reasoning_tokens}
    body = json.dumps(_b).encode()
    for a in range(5):
        try:
            req = urllib.request.Request(API, data=body,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"})
            with urllib.request.urlopen(req, timeout=90) as r:
                _m = json.loads(r.read())["choices"][0]["message"]
                out = (_m.get("content") or "") or (_m.get("reasoning_content") or "")
            with open(f"results/llm_api_log_{TAG}.jsonl", "a") as f:
                f.write(json.dumps({"cond": cond, "prompt_tail": prompt[-400:], "out": out}) + "\n")
            j = json.loads(out[out.index("{"):out.rindex("}") + 1])
            cfg = {}
            for k in GRID:  # snap to grid (missing keys fall back to baseline)
                v = j.get(k, BASE[k])
                if k == "act":
                    cfg[k] = v if v in GRID[k] else BASE["act"]
                else:
                    cfg[k] = min(GRID[k], key=lambda g: abs(math.log(g) - math.log(max(float(v), 1e-9))) if g > 0 else 9e9)
            return cfg
        except Exception:
            time.sleep(2 * (a + 1))
    return dict(BASE)


_STUB_CTR = {}
def _stub_propose(cond, confirmed, records):
    """Deterministic offline proposer for stub-testing enforcement mechanics (LLM_STUB=1).
    Cycles: valid fresh neighbors of BASE; every 3rd call re-proposes the first recorded config
    (exercises the enforcement block / soft retry); every 7th proposes a 2-step config (gate reject)."""
    i = _STUB_CTR[cond] = _STUB_CTR.get(cond, 0) + 1
    if records and i % 3 == 1:
        return json.loads(sorted(records)[0])
    if i % 7 == 3:
        cfg = dict(BASE); cfg["lr"] = GRID["lr"][0]; cfg["hidden"] = GRID["hidden"][0]
        return cfg  # two params off baseline: gate violation
    steps = [(k, d) for k in ("lr", "hidden", "alpha", "batch", "b1") for d in (-1, +1)]
    k, d = steps[(i * 2 + (7 if cond == "graded" else 0)) % len(steps)]
    g = GRID[k]; cfg = dict(BASE)
    try:
        cfg[k] = g[max(0, min(len(g) - 1, g.index(BASE[k]) + d))]
    except ValueError:
        cfg[k] = g[0]
    if cfg == BASE: cfg["b1"] = GRID["b1"][0]
    return cfg

def _is_neighbor(cfg, confirmed):
    """one-step-one-param neighbor of BASE or any confirmed config"""
    import json as _j
    anchors = [BASE] + [_j.loads(c) for c in confirmed]
    for a in anchors:
        diff = [k for k in GRID if cfg[k] != a[k]]
        if len(diff) == 0:
            return False  # exact repeat of an anchor: not a fresh proposal
        if len(diff) == 1:
            k = diff[0]
            ga = GRID[k]
            try:
                if abs(ga.index(cfg[k]) - ga.index(a[k])) == 1:
                    return True
            except ValueError:
                pass
    return False

def _ev(cond, rep, event, key, extra=None):
    with _LOCK, open(f"results/llm_events_{TAG}.jsonl", "a") as f:
        f.write(json.dumps({"cond": cond, "rep": rep, "event": event, "key": key, **(extra or {})}) + "\n")

def run_loop(cond, rep):
    SF = f"results/llm_state_{TAG}_{cond}_{rep}.json"
    st = json.load(open(SF)) if os.path.exists(SF) else dict(
        budget=BUDGET, confirmed=[], records={}, proposals=[], seed_ctr=0, parole_open=[])
    rng = np.random.default_rng(7000 + 100 * CONDS.index(cond) + rep)
    def seed():
        st["seed_ctr"] += 1
        return 500_000 + 50_000 * CONDS.index(cond) + 5_000 * rep + st["seed_ctr"]
    if os.path.exists(SF) and st["budget"] <= 1:
        return st  # terminal state (the loop's own break can end at budget 1); completed replicates stay frozen
    while st["budget"] > 0:
        parole_note = ""
        if cond == "parole" and st["records"]:
            reopen = [k for k in st["records"] if rng.random() < 0.05]
            if reopen:
                parole_note = "; ".join(", ".join(f"{p}={json.loads(k)[p]}" for p in GRID) for k in reopen[:3])
        blocked_note = ""
        if ENFORCE:
            locked = locked_keys(cond, st["records"], st.get("parole_open"))
            cfg = None
            for strike in range(3):  # blocked proposals cost no budget (the lock sits in front of the runner)
                cand = propose(cond, st["confirmed"], st["records"], parole_note,
                               [json.loads(p)["hidden"] for p in st["proposals"][-8:]] if st["proposals"] else [],
                               blocked_note)
                ckey = json.dumps(cand, sort_keys=True)
                if ckey not in locked:
                    cfg = cand; break
                st.setdefault("blocked", []).append(ckey)
                st.setdefault("enforce_blocks", 0); st["enforce_blocks"] += 1
                _ev(cond, rep, "block", ckey)
                short = ", ".join(f"{k}={cand[k]}" for k in GRID)
                blocked_note = f"\nYour previous proposal [{short}] was REJECTED by the enforcement layer (bank status DEAD/CLOSED). Propose a different config."
                json.dump(st, open(SF, "w"))
            if cfg is None:  # three consecutive blocked proposals: forfeit one slot to break the deadlock
                st["budget"] -= 1
                st.setdefault("enforce_forfeits", 0); st["enforce_forfeits"] += 1
                _ev(cond, rep, "forfeit", "")
                json.dump(st, open(SF, "w")); continue
        else:
            cfg = propose(cond, st["confirmed"], st["records"], parole_note,
                          [json.loads(p)["hidden"] for p in st["proposals"][-8:]] if st["proposals"] else [])
        key = json.dumps(cfg, sort_keys=True)
        st["proposals"].append(key)
        if GATED and not _is_neighbor(cfg, st["confirmed"]):
            st["budget"] -= 1  # slot lost, proposal discarded unscored (as stated in the prompt)
            st.setdefault("gate_rejects", 0); st["gate_rejects"] += 1
            _ev(cond, rep, "gate_reject", key)
            json.dump(st, open(SF, "w")); continue
        l1 = train(cfg, seed()); st["budget"] -= 1
        _ev(cond, rep, "train", key, {"locked_at_train": key in locked_keys(cond, st["records"], st.get("parole_open"))})
        if l1 >= BM:
            st["records"].setdefault(key, []).append(l1)
            _ev(cond, rep, "record", key, {"stage": "first"})
        else:
            if st["budget"] < 2: break
            v1, v2 = train(cfg, seed()), train(cfg, seed()); st["budget"] -= 2
            _ev(cond, rep, "verify", key)
            if (l1 + v1 + v2) / 3 < BM:
                if key not in st["confirmed"]:
                    st["confirmed"].append(key)
                    _ev(cond, rep, "confirm", key)
                else:
                    _ev(cond, rep, "confirm", key, {"dup": True})
            else:
                st["records"].setdefault(key, []).extend([l1, v1, v2])
                _ev(cond, rep, "record", key, {"stage": "verify"})
        json.dump(st, open(SF, "w"))
    json.dump(st, open(SF, "w"))
    return st

results = {}
_jobs = [(cond, rep) for cond in CONDS for rep in range(REPS)]
if _A.par <= 1:
    for cond, rep in _jobs:
        st = run_loop(cond, rep); results[f"{cond}-{rep}"] = st
        print(f"[{cond} rep{rep}] confirmed={len(st['confirmed'])} distinct_proposed={len(set(st['proposals']))}", flush=True)
else:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=_A.par) as _ex:
        _futs = {_ex.submit(run_loop, cond, rep): (cond, rep) for cond, rep in _jobs}
        for _f in as_completed(_futs):
            cond, rep = _futs[_f]; st = _f.result(); results[f"{cond}-{rep}"] = st
            print(f"[{cond} rep{rep}] confirmed={len(st['confirmed'])} distinct_proposed={len(set(st['proposals']))}", flush=True)

# truth: every distinct proposed config across ALL conditions (effect distribution + discoveries).
# Prior truth values are PRESERVED (extension runs must not re-measure and shift published replicates);
# only configs without a stored truth are tested.
distinct = sorted({p for st in results.values() for p in st["proposals"]})
_prior = {}
if os.path.exists(f"results/llm_loop_{TAG}.json"):
    _prior = json.load(open(f"results/llm_loop_{TAG}.json")).get("truth", {})
truth = {}
for i, key in enumerate(distinct):
    if key in _prior:
        truth[key] = _prior[key]; continue
    cfg = json.loads(key)
    truth[key] = float(np.mean([train(cfg, 900_000 + 10 * i + j) for j in range(4)]))
out = dict(BM=BM, SIG=SIG, budget=BUDGET, reps=REPS, results={k: dict(
    confirmed=v["confirmed"], proposals=v["proposals"]) for k, v in results.items()}, truth=truth)
json.dump(out, open(f"results/llm_loop_{TAG}.json", "w"), indent=1)

# headline numbers
print(f"\nbaseline {BM:.4f}±{SIG:.4f}; {len(distinct)} distinct proposed configs truth-tested")
effs = [(BM - truth[k]) / SIG for k in distinct]
good = [e for e in effs if e > 0]
marg = [e for e in good if e < 1.0]
print(f"LLM-proposed effect distribution: {len(good)}/{len(effs)} genuinely good; "
      f"marginal (<1σ) share of good ideas: {len(marg)}/{len(good)}")
for cond in CONDS:
    ds = [sum((BM - truth[c]) / SIG > 0 for c in results[f'{cond}-{r}']["confirmed"]) for r in range(REPS)]
    print(f"{cond:7s} truth-validated discoveries: {ds} (mean {np.mean(ds):.1f})")
