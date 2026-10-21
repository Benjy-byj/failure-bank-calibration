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

res = json.load(open(_p('v3_results.json', 'simulation')))
sigmas = ['0.5', '1.5', '3.0']
titles = ['Low noise σ/τ = 0.5\n(accurate verdicts)', 'High noise σ/τ = 1.5\n(autoresearch regime)', 'Extreme noise σ/τ = 3.0']

fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
for ax, sig, title in zip(axes, sigmas, titles):
    rows = np.array(res[sig]['rows']); cal = np.array(res[sig]['cal'])
    s, good = rows[:,0], rows[:,2]
    se_g = rows[:,6] * np.sqrt( (rows[:,2].std()+1e-9) )  # crude; recompute properly below
    # good-count SE not saved; approximate with sqrt(good)/sqrt(500) binomial-ish spread ~ use value se scaled — instead just plot means with light band from replicate std not available; skip band for counts, use se of value only where plotted
    ax.plot(s, good, 'o-', color='#1a6fb4', lw=2.2, ms=5, label='Fixed deference $s$ (naive bank)')
    ax.axhline(cal[1], color='#d1495b', ls='--', lw=2, label='Calibrated deference (evidence-weighted)')
    kmax = np.argmax(good)
    ax.plot(s[kmax], good[kmax], '*', color='#e8a628', ms=17, zorder=5)
    ax.set_title(title, fontsize=11.5, fontweight='bold')
    ax.set_xlabel('Sharing intensity $s$\n(P failure verdict is published & locks the idea)', fontsize=9.5)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
axes[0].set_ylabel('True discoveries per run\n(confirmed ideas with δ > 0)', fontsize=10.5)
axes[1].legend(fontsize=9, loc='lower center', framealpha=0.9)
fig.suptitle('Sharing failure verdicts helps — until it locks in wrongful convictions  (tree-structured idea model, B=800, 500 reps)',
             fontsize=12.5, fontweight='bold', y=1.04)
plt.tight_layout()
plt.savefig(_fig('inverted_u.png'), dpi=160, bbox_inches='tight')
print('saved')
