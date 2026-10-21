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

S = json.load(open(_p('summary.json')))
bm, bs = S['baseline']['mean'], S['baseline']['std']
names = list(S['verdicts'])
eff = {k: bm - S['truth'][k]['mean'] for k in names}
fails  = [k for k in names if not S['verdicts'][k]['pass']]
vfails = [k for k in names if S['verdicts'][k]['pass'] and S['verdicts'][k].get('confirmed') is False]
wrongA = [k for k in fails if eff[k] > 0]

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.5, 5.2), gridspec_kw={'width_ratios':[1.15,1]})
sig = bs
for k in names:
    x = -(S['verdicts'][k]['val_loss'] - bm)/sig; y = eff[k]/sig
    if k in wrongA: c,m,s_,z = '#d1495b','*',260,5
    elif k in fails: c,m,s_,z = '#8ea6b8','o',45,2
    elif k in vfails: c,m,s_,z = '#e8a628','s',60,3
    else: c,m,s_,z = '#2e7d32','o',55,3
    ax.scatter(x, y, c=c, marker=m, s=s_, zorder=z, edgecolors='white', linewidths=.5)
ax.axvline(0, color='#16212b', lw=1); ax.axhline(0, color='#16212b', lw=1)
ax.axvspan(-8.5, 0, color='#d1495b', alpha=0.05)
ax.annotate('wrongful convictions', xy=(-0.35, 0.35), xytext=(-5.6, 1.8), fontsize=9.5,
            fontweight='bold', color='#d1495b', arrowprops=dict(arrowstyle='->', color='#d1495b'))
ax.set_xlabel('Single-seed verdict (improvement, σ units)')
ax.set_ylabel('16-seed ground-truth effect (σ units)')
ax.set_title('A · First-round verdicts vs ground truth', fontsize=11, fontweight='bold')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([0],[0],marker='*',color='w',markerfacecolor='#d1495b',markersize=15,label='wrongful conviction'),
                   Line2D([0],[0],marker='o',color='w',markerfacecolor='#8ea6b8',markersize=8,label='rightful conviction'),
                   Line2D([0],[0],marker='s',color='w',markerfacecolor='#e8a628',markersize=8,label='verification fail'),
                   Line2D([0],[0],marker='o',color='w',markerfacecolor='#2e7d32',markersize=8,label='confirmed')],
          fontsize=8, loc='lower right')

# Panel B: pooled rates vs theory
cats = ['$W_A$\nsingle-shot\nconvictions\n(n=120)', '$W_B$\nverification\nconvictions\n(n=16)', 'false\nconfirmations\n(n=80)']
vals = [17.5, 50.0, 8.8]
lo = [11.7, 28.0, 4.3]; hi = [25.3, 72.0, 17.0]
theory = [19.0, 34.0, None]
xs = np.arange(3)
bars = ax2.bar(xs, vals, width=.55, color=['#8ea6b8','#e8a628','#2e7d32'],
        yerr=[np.array(vals)-np.array(lo), np.array(hi)-np.array(vals)], capsize=5)
for i, th in enumerate(theory):
    if th is not None:
        ax2.hlines(th, xs[i]-.34, xs[i]+.34, color='#16212b', lw=2.5, linestyle='--', zorder=5)
ax2.plot([],[], 'k--', lw=2.5, label='theory (empirical-prior MC)')
for i,v in enumerate(vals):
    ax2.text(xs[i], hi[i]+2, f"{v:.1f}%", ha='center', fontweight='bold', fontsize=11)
ax2.set_xticks(xs); ax2.set_xticklabels(cats, fontsize=9)
ax2.set_ylabel('Wrongful / false rate (%)'); ax2.set_ylim(0, 80)
ax2.set_title('B · Pooled rates (216 verdict events) vs theory', fontsize=11, fontweight='bold')
ax2.legend(fontsize=9)
for a in (ax, ax2): a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.suptitle('Live training-loop replay: wrongful convictions measured and predicted', fontsize=12.5, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(_fig('replay_fig2.png'), dpi=160, bbox_inches='tight')
print('ok')
