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

# v2 data
fresh=np.array([45,28,62,62,62,35]); weak=np.array([8,4,8,18,8,8])
near=np.array([18,8,18,28,18,12]); strong=np.array([3,2,3,4,3,2])
d_dead=np.array([8,12,8,8,8]); d_inc=np.array([35,28,35,30,35])

m=lambda a:(a.mean(),a.std(ddof=1)/np.sqrt(len(a)))
print("B: fresh %.1f±%.1f weak %.1f±%.1f near %.1f±%.1f strong %.1f±%.1f"%(*m(fresh),*m(weak),*m(near),*m(strong)))
r_w=weak/fresh; r_n=near/fresh; r_s=strong/fresh
print("within-trial ratios: weak/fresh %.3f±%.3f  near/fresh %.3f±%.3f  strong/fresh %.3f±%.3f"%(*m(r_w),*m(r_n),*m(r_s)))
t,p=stats.ttest_ind(d_inc,d_dead,equal_var=False)
u,pu=stats.mannwhitneyu(d_inc,d_dead,alternative='greater')
print("D label effect: DEAD %.1f±%.1f vs INCONCLUSIVE %.1f±%.1f | gap %.1fpp | Welch t=%.1f p=%.2g | MWU p=%.4f"%(*m(d_dead),*m(d_inc),d_inc.mean()-d_dead.mean(),t,p,pu))
print("A behavioral: v1 0/10 + v2 0/10 = 0/20; rule-of-three 95%% upper bound = %.0f%%"%(100*3/20))
print("consistency: TaskB weak (DEAD in full bank) %.1f vs TaskD DEAD %.1f"%(weak.mean(),d_dead.mean()))

fig,axes=plt.subplots(1,2,figsize=(11,4.3))
ax=axes[0]
names=['FRESH\n(anchor)','WEAK\n(DEAD label)','NEAR-MISS\n(DEAD label)','STRONG\n(DEAD label)']
vals=[fresh.mean(),weak.mean(),near.mean(),strong.mean()]
errs=[m(x)[1] for x in (fresh,weak,near,strong)]
cols=['#8ea6b8','#e8a628','#2e7d32','#d1495b']
ax.bar(names,vals,yerr=errs,color=cols,capsize=4)
ax.set_ylabel('Stated P(genuine improvement) %')
ax.set_title('B · Stated beliefs with prior anchor\n(behavioral revisits of DEAD ideas: 0/20 across v1+v2)',fontsize=10.5,fontweight='bold')
ax=axes[1]
ax.bar(['Status: DEAD','Status:\nINCONCLUSIVE'],[d_dead.mean(),d_inc.mean()],
       yerr=[m(d_dead)[1],m(d_inc)[1]],color=['#d1495b','#1a6fb4'],capsize=4,width=.55)
ax.set_ylabel('Stated P(genuine improvement) %')
ax.set_title('D · Pure label effect — identical evidence line\n(+0.12%%, 1 seed, sub-noise): 8.8%% vs 32.6%%, p<0.001',fontsize=10.5,fontweight='bold')
ax.annotate('3.7×',xy=(0.5,20),ha='center',fontsize=16,fontweight='bold',color='#16212b')
for a in axes: a.spines['top'].set_visible(False); a.spines['right'].set_visible(False)
fig.suptitle('A deployed agent prices evidence — until the label overrides the arithmetic  (claude-sonnet-4-6, pilot v1+v2)',fontsize=12,fontweight='bold',y=1.03)
plt.tight_layout(); plt.savefig(_fig('pilot_fig.png'),dpi=160,bbox_inches='tight')
print('fig saved')
