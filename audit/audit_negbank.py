"""In-situ audit of the released negative-knowledge bank of [1] (github.com/hch-wang/Negative_Knowledge).
Recomputes every number in App. D from the public artifact. Usage: python3 audit_negbank.py <path-to-clone>"""
import json, glob, re, os, sys, collections
root = sys.argv[1] if len(sys.argv) > 1 else "."
S = os.path.join(root, "reproduction", "section4")
recs = {f.split('/')[-1][:-5]: json.load(open(f)) for f in sorted(glob.glob(f"{S}/logs/nk_records/*_r*.json"))}
print(f"per-round records: {len(recs)}")
print("scope:", dict(collections.Counter(r['failure'].get('scope') for r in recs.values())))
print("action:", dict(collections.Counter(r['failure'].get('recommended_action') for r in recs.values())))
num_fields = [k for r in recs.values() for k, v in r['failure'].items() if isinstance(v, (int, float))]
print("numeric fields inside failure blocks:", len(num_fields))
pos = {k for k, r in recs.items() if r['rationale'].lstrip().lower().startswith('positive')}
print(f"curator-labeled positive findings typed as failures: {len(pos)}/{len(recs)} -> {sorted(pos)}")
neg = [json.loads(l) for l in open(f"{S}/logs/banks/bank_negative.jsonl")]
posb = [json.loads(l) for l in open(f"{S}/logs/banks/bank_positive.jsonl")]
inneg = [k for k in pos if any(recs[k]['attempted_route'][:60] in e.get('attempted_route', '') for e in neg)]
print(f"negative bank: {len(neg)} entries; positive bank: {len(posb)}; positives routed INTO negative bank: {len(inneg)}/{len(pos)} -> {inneg}")
code = open(os.path.join(root, "negative_knowledge", "runtime.py")).read() + open(os.path.join(root, "negative_knowledge", "curator.py")).read()
print("retire/revise/reopen/confidence mechanisms in runtime+curator:", len(re.findall(r"retire|revis|reopen|overturn|confidence", code, re.I)))
for task in ("T_A", "T_B", "T_C"):
    for cond in ("NoKB", "PosOnly", "NegOnly", "PosNeg"):
        d = f"{S}/logs/stage2/{task}/{cond}"
        r = open(f"{d}/reasoning.md").read() if os.path.exists(f"{d}/reasoning.md") else ""
        ev = json.load(open(f"{d}/verified_eval.json")) if os.path.exists(f"{d}/verified_eval.json") else {}
        cites = set(re.findall(r"`(kb-[A-Za-z0-9_\-\.]+)`", r))
        rej = sum(1 for l in r.split("\n") if re.search(r"reject", l, re.I) and "kb-" in l)
        print(f"  {task} {cond:8s} useful={ev.get('useful')!s:5s} distinct-cites={len(cites):2d} rejection-lines={rej}")
m = open(f"{S}/logs/stage2/T_A/NegOnly/memory.md").read().split("\n")[2]
print("consumer instruction:", m[:120])
