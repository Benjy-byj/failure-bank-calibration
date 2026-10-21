import os
import numpy as np
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
def _fig(name):
    d = _ROOT / 'figures_out'; d.mkdir(exist_ok=True); return str(d / name)

import matplotlib.pyplot as plt
from scipy.stats import norm
plt.style.use('seaborn-v0_8-whitegrid')

# pasted results: per task, buckets [(0,.25],(.25,.5],(.5,1],(1,2],(2,inf)] -> (p, n)
tasks = {
 'slice':      [(.441,204),(.323,198),(.364,456),(.214,976),(.012,29270)],
 'naval':      [(.491,116),(.379,124),(.323,232),(.274,544),(.023,30088)],
 'parkinsons': [(.433,254),(.420,264),(.282,507),(.181,1058),(.011,29021)],
 'protein':    [(.424,262),(.321,237),(.243,489),(.129,1081),(.010,29035)],
}
mids = [0.125, 0.375, 0.75, 1.5, 3.5]
cols = {'slice':'#1a6fb4','naval':'#2e7d32','parkinsons':'#e8a628','protein':'#d1495b'}
fig, ax = plt.subplots(figsize=(7.6, 5))
x = np.linspace(0.01, 5, 300)
ax.plot(x, norm.cdf(-x), 'k-', lw=2.5, label=r'theory: $P(\mathrm{convict}\mid\delta)=\Phi(-\delta/\sigma)$', zorder=2)
for t, rows in tasks.items():
    ps = [r[0] for r in rows]; ns = [r[1] for r in rows]
    se = [1.96*np.sqrt(p*(1-p)/n) for p, n in rows]
    ax.errorbar(mids, ps, yerr=se, fmt='o', color=cols[t], ms=6, capsize=3, label=f'FCNet {t}', alpha=.9, zorder=3)
# pooled first bucket annotation
ax.annotate('near-marginal true improvements:\nconvicted 44% of the time\n(theory: 45%)', xy=(0.125, 0.44), xytext=(1.1, 0.62),
            fontsize=9.5, fontweight='bold', arrowprops=dict(arrowstyle='->', color='#16212b'))
ax.text(2.6, 0.24, 'points above the curve at mid-range:\ntruth estimated from 3 seeds\n(attenuation leakage; see text)', fontsize=8.5, color='#5c6b7a')
ax.set_xlabel('True improvement (σ units)'); ax.set_ylabel('P(convicted by single-seed verdict)')
ax.set_xlim(0, 5); ax.set_ylim(0, 0.75)
ax.set_title('Convictions hunt marginal truth: 122,817 single-seed verdicts\nacross four public HPO benchmark tasks (FCNet)', fontsize=11.5, fontweight='bold')
ax.legend(fontsize=9); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.savefig(_fig('fcnet_fig.png'), dpi=160, bbox_inches='tight')
# pooled stats
wr = 877+1005+884+724; cv = 30789+30357+30866+30805
print(f"pooled W_A {wr}/{cv} = {wr/cv:.4f}; first-bucket pooled p = 0.440 vs theory 0.450")
