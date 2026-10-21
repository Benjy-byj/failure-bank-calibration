import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
def _fig(name):
    d = _ROOT / 'figures_out'; d.mkdir(exist_ok=True); return str(d / name)
plt.style.use('seaborn-v0_8-whitegrid')

# family, choice(marked picks under DEAD / n, under INCONCLUSIVE / n), beliefs(dead, dead_prov, inconclusive), type
D = [
 ("Claude Haiku 4.5",  (0,6),(6,6),  7.0, 22.7, 22.8, "unlock"),
 ("Claude Sonnet 4.6", (0,6),(6,6),  7.2, 18.0, 25.6, "unlock"),
 ("Claude Opus 4.8",   (0,6),(6,6),  6.3, 23.2, 25.6, "unlock"),
 ("DeepSeek-R1",       (1,6),(6,6),  1.5, 50.0, 50.0, "unlock"),
 ("DeepSeek-chat",     (1,6),(6,6),  4.3,  1.3, 23.0, "hard"),
 ("GPT-4o",            (0,6),(6,6),  0.0,  0.0, 31.4, "hard"),
 ("Llama-4-Scout",     (2,6),(6,6), 55.6, 26.3, 40.7, "hard"),
 ("GLM-4.7",           (0,6),(5,6), 21.1, 21.0, 21.0, "calib"),
 ("Kimi-K2",           (3,6),(5,6), 15.6, 12.1, 17.0, "immune"),
 ("Qwen3-32B",         (0,6),(4,6), None, None, None, "immune"),
 ("Gemini-2.5-flash",  (3,6),(6,6),  0.5,  0.0,  2.8, "floor"),
 ("Mistral-medium-3",  (2,6),(6,6),  0.0,  0.0,  2.4, "floor"),
]
TYPE = {"unlock":("#2e7d32","provenance-unlockable"), "hard":("#d1495b","hard-locked"),
        "calib":("#7b3fa0","calibrated, choice-locked"), "immune":("#1a6fb4","near-immune"),
        "floor":("#8a8f98","floor-dominated")}

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.2, 5.9), gridspec_kw={'width_ratios':[1,1.12]})
ys = np.arange(len(D))[::-1]

# Panel A: choice flip
for y,(name,(dm,dn),(im,inn),bd,bp,bi,t) in zip(ys, D):
    col = TYPE[t][0]
    xd, xi = 100*dm/dn, 100*im/inn
    ax.plot([xd, xi], [y, y], color=col, lw=2.4, alpha=.55, zorder=1)
    ax.scatter(xd, y, marker='o', s=95, facecolor='white', edgecolor=col, lw=2.2, zorder=3)
    ax.scatter(xi, y, marker='o', s=95, color=col, zorder=3)
    ax.annotate(f"{dm}/{dn}", (xd, y), textcoords="offset points", xytext=(-4, 9), ha='right',
                fontsize=7.6, color=col)
    ax.annotate(f"{im}/{inn}", (xi, y), textcoords="offset points", xytext=(4, 9), ha='left',
                fontsize=7.6, color=col, fontweight='bold')
ax.set_yticks(ys); ax.set_yticklabels([d[0] for d in D], fontsize=9.5)
ax.set_xlim(-14, 118); ax.set_xlabel('Selection of the a-priori-best idea (% of trials)')
ax.set_title('A · Choice: the label suppresses selection of the a-priori-best idea\nin every tested family (raw counts shown; 5--6 trials/condition)',
             fontsize=11, fontweight='bold')
ax.axvline(50, color='#c9d1d9', lw=1, ls=':')
ax.legend(handles=[Line2D([0],[0],marker='o',color='w',markerfacecolor='white',markeredgecolor='#16212b',
                          markeredgewidth=2,markersize=10,label='status: DEAD'),
                   Line2D([0],[0],marker='o',color='w',markerfacecolor='#16212b',markersize=10,
                          label='status: INCONCLUSIVE')], fontsize=8.5, loc='lower right')

# Panel B: beliefs
w = 0.26
for y,(name,_,_,bd,bp,bi,t) in zip(ys, D):
    col = TYPE[t][0]
    if bd is None:
        ax2.text(1.5, y, "belief probes did not parse", fontsize=8, style='italic',
                 color='#8a8f98', va='center'); continue
    ax2.barh(y+w, bi, height=w, color=col, alpha=.30)
    ax2.barh(y,   bp, height=w, color=col, alpha=.62)
    ax2.barh(y-w, bd, height=w, color=col, alpha=1.0)
ax2.axvline(21.2, color='#16212b', lw=1.8, ls='--', zorder=5)
ax2.text(20.2, ys[0]+1.2, 'Bayesian posterior $\\Phi(-0.8)=21.2\\%$', fontsize=8.5, fontweight='bold', va='top', ha='right')
ax2.set_yticks(ys); ax2.set_yticklabels([])
seen = set()
for y,(name,_,_,bd,bp,bi,t) in zip(ys, D):
    if t in seen: continue
    seen.add(t)
    mem = [yy for yy,dd in zip(ys, D) if dd[6]==t]; ymid = max(mem) if t=='floor' else np.mean(mem)
    ax2.annotate(TYPE[t][1], xy=(61.5, ymid), xytext=(61.5, ymid), fontsize=8.6, fontweight='bold',
                 color=TYPE[t][0], ha='right', va='center',
                 bbox=dict(boxstyle='round,pad=0.25', fc='white', ec=TYPE[t][0], lw=1, alpha=.9))
ax2.set_xlabel('Stated P(genuine improvement) %')
ax2.set_xlim(0, 62)
ax2.set_title('B · Belief: response patterns are heterogeneous\nsame model order as panel A; identical evidence in all conditions',
              fontsize=11, fontweight='bold')
ax2.legend(handles=[Line2D([0],[0],marker='s',color='w',markerfacecolor='#16212b',markersize=9,label='DEAD'),
                    Line2D([0],[0],marker='s',color='w',markerfacecolor='#16212b',alpha=.62,markersize=9,label='DEAD + provenance note'),
                    Line2D([0],[0],marker='s',color='w',markerfacecolor='#16212b',alpha=.30,markersize=9,label='INCONCLUSIVE')],
           fontsize=8.2, loc='upper right', bbox_to_anchor=(1.0, 0.99), framealpha=.95)
for a in (ax, ax2):
    a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.suptitle('Twelve models, nine families: belief responses differ, choice suppression replicates in all of them',
             fontsize=13, fontweight='bold', y=1.005)
plt.tight_layout()
plt.savefig(_fig('xfam_fig.png'), dpi=160, bbox_inches='tight')
print("saved")
