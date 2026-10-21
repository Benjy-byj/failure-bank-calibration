import os
import json, numpy as np
from scipy.stats import norm, multivariate_normal as mvn
from scipy.special import ndtr
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
bm, bs, nb = S['baseline']['mean'], S['baseline']['std'], S['baseline']['n']
names = list(S['verdicts'])
eff = {}; se_eff = {}
for k in names:
    t = S['truth'][k]
    eff[k] = bm - t['mean']                       # >0 = genuine improvement
    se_eff[k] = np.sqrt(t['std']**2/t['n'] + bs**2/nb)
E = np.array([eff[k] for k in names])
sig = bs                                          # per-run noise
truth_stds = [S['truth'][k]['std'] for k in names if S['truth'][k]['std'] < 0.02]
sig_pooled = float(np.mean(truth_stds))
print(f"sigma_run: baseline {sig:.5f}, pooled truth {sig_pooled:.5f}; tau_hat {E.std(ddof=1):.5f}; mu0_hat {E.mean():+.5f}; sigma/tau = {sig/E.std(ddof=1):.2f}")

fails  = [k for k in names if not S['verdicts'][k]['pass']]
vfails = [k for k in names if S['verdicts'][k]['pass'] and S['verdicts'][k].get('confirmed') is False]
confs  = [k for k in names if S['verdicts'][k].get('confirmed')]
wrongA = [k for k in fails if eff[k] > 0]
wrongA_exp = sum(ndtr(eff[k]/se_eff[k]) for k in fails)
print(f"\nsingle-shot FAILs: {len(fails)} | point wrongful: {len(wrongA)} ({', '.join(wrongA)})")
print(f"empirical W_A: point {len(wrongA)/len(fails):.2f} | measurement-error-aware {wrongA_exp/len(fails):.2f} (expected {wrongA_exp:.1f}/{len(fails)})")
print(f"verification FAILs: {len(vfails)} ({', '.join(vfails)}) | wrongful: {sum(eff[k]>0 for k in vfails)} | W_B expectation-aware {sum(ndtr(eff[k]/se_eff[k]) for k in vfails)/max(1,len(vfails)):.2f}")
print(f"confirmed: {len(confs)} | truly good among confirmed: {sum(eff[k]>0 for k in confs)} -> false-confirm rate {sum(eff[k]<=0 for k in confs)}/{len(confs)}")
g = sum(e>0 for e in E)
print(f"truly good ideas: ~{g}/36; pipeline found {sum(eff[k]>0 for k in confs)}, wrongfully locked ~{len(wrongA)} -> miss rate locked in ≈ {len(wrongA)/g:.0%}")
print(f"wrongful effects (in sigma units): {[round(eff[k]/sig,2) for k in wrongA]}  <-- all marginal, Thm 1(c)")
print(f"forfeited stacked gain: {sum(eff[k] for k in wrongA):.4f} = {sum(eff[k] for k in wrongA)/sig:.1f} sigma")

# theory W_A: (i) Gaussian plug-in, (ii) empirical-prior Monte Carlo
mu0h, tauh = E.mean(), E.std(ddof=1)
rho = tauh/np.sqrt(tauh**2+sig**2)
WA_gauss = mvn(mean=[0,0], cov=[[1,-rho],[-rho,1]]).cdf([mu0h/tauh, -mu0h/np.sqrt(tauh**2+sig**2)]) / ndtr(-mu0h/np.sqrt(tauh**2+sig**2))
rng = np.random.default_rng(0); M = 400000
e_mc = rng.choice(E, M) + rng.normal(0, np.mean([se_eff[k] for k in names]), M)  # smooth empirical prior
obs = e_mc + rng.normal(0, sig, M)
selA = obs <= 0
WA_emp = (e_mc[selA] > 0).mean()
x1 = e_mc + rng.normal(0, sig, M); v2 = e_mc[:,None] + rng.normal(0, sig, (M,2))
selB = (x1 > 0) & ((x1 + v2.sum(1))/3 <= 0)
WB_emp = (e_mc[selB] > 0).mean()
print(f"\ntheory W_A: Gaussian plug-in {WA_gauss:.2f} | empirical-prior MC {WA_emp:.2f} | measured {wrongA_exp/len(fails):.2f}")
print(f"theory W_B (empirical-prior MC): {WB_emp:.2f} | measured 0/{len(vfails)} (n too small; P(0 of 4 | W_B={WB_emp:.2f}) = {(1-WB_emp)**4:.2f})")

# figure
fig, ax = plt.subplots(figsize=(7.6, 5.6))
vd = {k: S['verdicts'][k]['val_loss'] - bm for k in names}
for k in names:
    x, y = -vd[k]/sig, eff[k]/sig
    if k in wrongA: c, m, s_, z = '#d1495b', '*', 260, 5
    elif k in fails: c, m, s_, z = '#8ea6b8', 'o', 45, 2
    elif k in vfails: c, m, s_, z = '#e8a628', 's', 60, 3
    else: c, m, s_, z = '#2e7d32', 'o', 55, 3
    ax.scatter(x, y, c=c, marker=m, s=s_, zorder=z, edgecolors='white', linewidths=.5)
ax.axvline(0, color='#16212b', lw=1); ax.axhline(0, color='#16212b', lw=1)
ax.axvspan(-8.5, 0, color='#d1495b', alpha=0.05)
ax.text(-4.2, 3.0, 'CONVICTED\n(single-seed verdict FAIL)', ha='center', fontsize=9, color='#a63d40')
ax.annotate('wrongful convictions:\ngenuinely good, locked forever', xy=(-0.35, 0.35), xytext=(-5.6, 1.6),
            fontsize=9.5, fontweight='bold', color='#d1495b',
            arrowprops=dict(arrowstyle='->', color='#d1495b'))
ax.set_xlabel('Single-seed verdict (improvement, σ units)')
ax.set_ylabel('Ground truth: 16-seed effect (σ units)')
ax.set_title('Empirical wrongful convictions in a live training loop\n36 mutations · A100 · verdicts vs 16-seed ground truth', fontsize=11.5, fontweight='bold')
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([0],[0],marker='*',color='w',markerfacecolor='#d1495b',markersize=16,label='wrongful conviction (4)'),
                   Line2D([0],[0],marker='o',color='w',markerfacecolor='#8ea6b8',markersize=8,label='rightful conviction'),
                   Line2D([0],[0],marker='s',color='w',markerfacecolor='#e8a628',markersize=8,label='verification fail'),
                   Line2D([0],[0],marker='o',color='w',markerfacecolor='#2e7d32',markersize=8,label='confirmed')],
          fontsize=8.5, loc='lower right')
ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
plt.tight_layout(); plt.savefig(_fig('replay_fig.png'), dpi=160, bbox_inches='tight')
print('fig saved')
