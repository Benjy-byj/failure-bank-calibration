import os
import json, numpy as np, matplotlib.pyplot as plt
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
H = json.load(open(_p('horizon.json', 'simulation')))
fig, ax = plt.subplots(figsize=(7.5,4.6))
cols={'1.5|0.6':'#d1495b','2.0|0.9':'#e8a628','1.0|0.9':'#2e7d32'}
labs={'1.5|0.6':'subcritical  λ=0.83, q_ext=1.00',
      '2.0|0.9':'near-critical λ=1.07, q_ext=0.93',
      '1.0|0.9':'supercritical λ=1.24, q_ext=0.79'}
for k,d in H.items():
    ax.plot(d['Bs'], d['depths'], 'o-', lw=2.2, ms=6, color=cols[k], label=labs[k])
ax.set_xscale('log'); ax.set_xticks([200,400,800,1600,3200]); ax.set_xticklabels([200,400,800,1600,3200])
ax.set_xlabel('Horizon B (total experiments)')
ax.set_ylabel('Discovery loss at full sharing (%)\n(U-depth)')
ax.set_title('Perfect memory costs more the longer you run:\nU-depth grows with horizon, ordered by lineage extinction probability', fontsize=11.5, fontweight='bold')
ax.legend(fontsize=9); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.savefig(_fig('horizon.png'), dpi=160, bbox_inches='tight')
print('ok')
