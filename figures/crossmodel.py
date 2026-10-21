import os
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
def _fig(name):
    d = _ROOT / 'figures_out'; d.mkdir(exist_ok=True); return str(d / name)
plt.style.use('seaborn-v0_8-whitegrid')

M = {
 'sonnet-4-6': dict(fresh=[45,28,62,62,62,35], weak=[8,4,8,18,8,8], near=[18,8,18,28,18,12], strong=[3,2,3,4,3,2],
                    dead=[8,12,8,8,8], inc=[35,28,35,30,35], A_dead=0, A_n=10+10),  # incl v1
 'haiku-4.5':  dict(fresh=[62,40,60,62,35,35], weak=[8,12,18,8,5,12], near=[18,8,8,18,8,8], strong=[3,4,4,3,2,4],
                    dead=[12,8,8,8,8], inc=[35,35,30,35,28], A_dead=0, A_n=10),
 'opus-4-8':   dict(fresh=[55,35,62,35,35,62], weak=[8,8,8,5,12,12], near=[15,12,18,8,15,18], strong=[3,3,3,2,3,3],
                    dead=[8,8,8,4,12], inc=[35,35,22,35,35], A_dead=0, A_n=10),
}
m=lambda a:(np.mean(a),np.std(a,ddof=1)/np.sqrt(len(a)))
print(f"{'model':12s} {'fresh':>10s} {'weak':>9s} {'near':>9s} {'strong':>8s} | {'DEAD':>9s} {'INCONC':>9s} {'gap':>6s} {'MWU p':>7s} | A revisits")
tot_dead=[]; tot_inc=[]; totA=0; totN=0
for k,d in M.items():
    u,p=stats.mannwhitneyu(d['inc'],d['dead'],alternative='greater')
    print(f"{k:12s} {m(d['fresh'])[0]:5.1f}±{m(d['fresh'])[1]:3.1f} {m(d['weak'])[0]:4.1f}±{m(d['weak'])[1]:3.1f} "
          f"{m(d['near'])[0]:4.1f}±{m(d['near'])[1]:3.1f} {m(d['strong'])[0]:3.1f}±{m(d['strong'])[1]:3.1f} | "
          f"{m(d['dead'])[0]:4.1f}±{m(d['dead'])[1]:3.1f} {m(d['inc'])[0]:4.1f}±{m(d['inc'])[1]:3.1f} "
          f"{np.mean(d['inc'])-np.mean(d['dead']):5.1f} {p:7.4f} | {d['A_dead']}/{d['A_n']}")
    tot_dead+=d['dead']; tot_inc+=d['inc']; totA+=d['A_dead']; totN+=d['A_n']
t,p=stats.ttest_ind(tot_inc,tot_dead,equal_var=False)
print(f"\nPOOLED: DEAD {np.mean(tot_dead):.1f} vs INCONCLUSIVE {np.mean(tot_inc):.1f} (n=15/15), Welch t={t:.1f} p={p:.2g}")
print(f"POOLED behavioral revisits: {totA}/{totN} (rule-of-three 95% upper {300/totN:.1f}%)")
nw = {k: np.mean(d['near'])-np.mean(d['weak']) for k,d in M.items()}
print(f"near-minus-weak narrative premium: {nw}")

fig,ax=plt.subplots(figsize=(7.8,4.4))
x=np.arange(3); w=0.34
names=list(M.keys())
dm=[np.mean(M[k]['dead']) for k in names]; de=[m(M[k]['dead'])[1] for k in names]
im=[np.mean(M[k]['inc']) for k in names];  ie=[m(M[k]['inc'])[1] for k in names]
ax.bar(x-w/2,dm,w,yerr=de,color='#d1495b',capsize=4,label='Status: DEAD')
ax.bar(x+w/2,im,w,yerr=ie,color='#1a6fb4',capsize=4,label='Status: INCONCLUSIVE')
for i in range(3):
    ax.text(i, max(im[i],dm[i])+2.5, f"{im[i]-dm[i]:.0f}pp", ha='center', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(names)
ax.set_ylabel('Stated P(genuine improvement) %')
ax.set_title('The label effect is capability-invariant within the Claude family\n(identical evidence line; behavioral revisits 0/40 pooled)',fontsize=11,fontweight='bold')
ax.legend(); ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.savefig(_fig('crossmodel_fig.png'),dpi=160,bbox_inches='tight')
print('fig saved')
