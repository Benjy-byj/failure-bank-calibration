import os
import json, numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
def _fig(name):
    d = _ROOT / 'figures_out'; d.mkdir(exist_ok=True); return str(d / name)
plt.style.use('seaborn-v0_8-whitegrid')
S = json.load(open(_p('results/sysloop.json', 'sysloop')))
BM, SIG = S['BM'], S['SIG']
truth = S['truth']
CONDS = ["nomem", "binary", "graded", "parole"]
LAB = {"nomem":"no memory","binary":"binary DEAD","graded":"evidence-graded","parole":"parole 5%"}
COL = {"nomem":"#8ea6b8","binary":"#d1495b","graded":"#2e7d32","parole":"#e8a628"}
disc = {c: [] for c in CONDS}; effs = {c: [] for c in CONDS}
for c in CONDS:
    for rep in range(3):
        st = S['state'][f"{c}-{rep}"]
        e = [(BM - truth[str(cf)])/SIG for cf in st['confirmed']]
        disc[c].append(sum(x > 0 for x in e))
        effs[c] += [x for x in e if x > 0]
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.6))
xs = np.arange(4)
means = [np.mean(disc[c]) for c in CONDS]
ax.bar(xs, means, width=.6, color=[COL[c] for c in CONDS], alpha=.85)
for i, c in enumerate(CONDS):
    ax.scatter([i]*3, disc[c], color='#16212b', zorder=5, s=28)
    ax.text(i, means[i]+2.2, f"{means[i]:.1f}", ha='center', fontweight='bold', fontsize=11)
ax.set_xticks(xs); ax.set_xticklabels([LAB[c] for c in CONDS], fontsize=9.5)
ax.set_ylabel('Truth-validated discoveries (per 220-run budget)')
ax.set_title('A · Same budget, four memory rules\n(3 replicate loops each; dots = individual loops)', fontsize=10.5, fontweight='bold')
for c in CONDS:
    srt = np.sort(effs[c]); ax2.plot(srt, np.linspace(0, 1, len(srt)), color=COL[c], lw=2.2, label=f"{LAB[c]} (n={len(srt)})")
ax2.set_xlabel('Discovery true effect (σ units)'); ax2.set_ylabel('ECDF')
ax2.set_title('B · Discovery-quality distribution\n(graded shifts right: spared marginals seed better lineages)', fontsize=10.5, fontweight='bold')
ax2.legend(fontsize=8.5)
for a in (ax, ax2): a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.suptitle('End-to-end closed loop: real verdicts, real cumulative supply, only the memory rule differs', fontsize=12, fontweight='bold', y=1.04)
plt.tight_layout(); plt.savefig(_fig('sysloop_fig.png'), dpi=160, bbox_inches='tight')
print('fig saved')
