"""Create logs/stage2/<task>/NegCal/{prompt.md,memory.md,meta.json} from the saved NegOnly cells by editing
the memory block IN PLACE: swap the preface, append one status line per entry derived from the entry's own
rendered `failure: ... scope=..., action=...` line (deep syntheses and evidence-free entries -> OPEN).
No entry text is altered. Run inside reproduction/section4."""
import re, json, pathlib, difflib
HEAD = "## Memory: negative-knowledge bank"
OLD_PREFACE = re.compile(r"Entries describe methods/regimes that FAILED\. Use to avoid pitfalls\..*?single-round failure logs\.", re.S)
def status_for(entry_text):
    if "[DEEP SYNTHESIS" in entry_text:
        return "  status: OPEN — path-level synthesis from 3 rounds at fixed settings; outside those settings it is a hypothesis, not a prohibition"
    m = re.search(r"failure: layer=[^,]*, scope=([\w_]*), action=([\w_]*)", entry_text)
    if m:
        scope, action = m.group(1), m.group(2)
        if scope == "general_failure" and action in ("abandon_route", "change_method"):
            return "  status: CLOSED (general mechanism stated); retry only with a stated reason the mechanism does not apply"
        if scope in ("regime_bound_failure", "local_failure"):
            return "  status: OPEN outside the stated regime — advisory only; this route may be retried for a different equation, horizon, or parameter range"
    return "  status: OPEN — no replicate evidence recorded; treat the rationale as a hypothesis"
def calibrate(txt):
    i = txt.index(HEAD)
    j = txt.find("\n## ", i + len(HEAD)); j = len(txt) if j < 0 else j
    block = txt[i:j]
    parts = re.split(r"(?m)^(?=### )", block)   # parts[0] = header+preface, rest = entries
    entries = parts[1:]
    n_closed = sum("CLOSED" in status_for(e) for e in entries)
    head = OLD_PREFACE.sub(
        "Each entry is a verdict from a small number of runs under specific settings; none carries replicate evidence. "
        f"Read the status line: {n_closed} entries are CLOSED (a general mechanism was stated) and the rest are OPEN. "
        "OPEN entries are regime-bound observations — outside their stated regime they are NOT prohibitions, and retrying them "
        "with a stated reason is legitimate. Do not rule out a method class on the strength of an OPEN entry alone.", parts[0], count=1)
    assert head != parts[0], "preface not found"
    new_entries = [e.rstrip("\n") + "\n" + status_for(e) + "\n" + ("\n" if e.endswith("\n\n") else "") for e in entries]
    return txt[:i] + head + "".join(new_entries) + txt[j:], len(entries), n_closed
S2 = pathlib.Path("logs/stage2")
for task in ("T_A", "T_B", "T_C"):
    src, dst = S2 / task / "NegOnly", S2 / task / "NegCal"; dst.mkdir(parents=True, exist_ok=True)
    for fn in ("prompt.md", "memory.md"):
        txt = (src / fn).read_text(); new, n, c = calibrate(txt); (dst / fn).write_text(new)
        d = [l for l in difflib.unified_diff(txt.splitlines(), new.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        print(f"{task}/{fn}: entries={n} CLOSED={c} diff-lines={len(d)}")
    if (src / "meta.json").exists():
        m = json.load(open(src / "meta.json")); m["condition"] = "NegCal"; json.dump(m, open(dst / "meta.json", "w"), indent=1)
