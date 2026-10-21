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

AB = json.load(open(_p('scan_AB.json', 'simulation')))
PH = json.load(open(_p('phase.json', 'simulation')))
LAM = json.load(open(_p('lambda.json', 'simulation')))

fig, axes = plt.subplots(2, 2, figsize=(12.5, 9))

# A) b-scan: good discoveries vs s
ax = axes[0,0]
cols = {'0.0':'#7f8c8d', '0.3':'#1a6fb4', '0.6':'#d1495b', '0.9':'#2e7d32'}
for b, dd in AB['b_scan'].items():
    r = np.array(dd['rows'])
    ax.plot(r[:,0], r[:,2], 'o-', color=cols[b], lw=2, ms=4, label=f'lineage coupling b={b}')
ax.set_xlabel('Sharing intensity $s$'); ax.set_ylabel('True discoveries')
ax.set_title('A · Inverted U exists even at b=0 (supply gating alone);\ndepth is non-monotone in heritability', fontsize=10.5, fontweight='bold')
ax.legend(fontsize=8.5)

# B) w-scan: value metric
ax = axes[0,1]
wcols = {'40':'#2e7d32','80':'#1a6fb4','200':'#e8a628','1000000000':'#d1495b'}
wlab = {'40':'w=40','80':'w=80','200':'w=200','1000000000':'w=∞ (false positives never caught)'}
for w, dd in AB['w_scan'].items():
    r = np.array(dd['rows'])
    ax.plot(r[:,0], r[:,1], 'o-', color=wcols[w], lw=2, ms=4, label=wlab[w])
ax.set_xlabel('Sharing intensity $s$'); ax.set_ylabel('Research value (time-weighted)')
ax.set_title('B · U collapses only when false positives are\nnever corrected — the asymmetry is the mechanism', fontsize=10.5, fontweight='bold')
ax.legend(fontsize=8.5)

# C) phase heatmap + criticality contour
ax = axes[1,0]
sigmas = [0.5,1.0,1.5,2.0,2.5]; bs = [0.0,0.3,0.6,0.9]
D = np.zeros((len(sigmas), len(bs))); L = np.zeros_like(D)
for i,s_ in enumerate(sigmas):
    for j,b_ in enumerate(bs):
        r = np.array(PH[f"{s_}|{b_}"]['rows']); g = r[:,2]
        D[i,j] = (g.max()-g[-1])/g.max()*100
        L[i,j] = LAM[f"{s_}|{b_}"]
im = ax.imshow(D, origin='lower', aspect='auto', cmap='RdYlBu_r',
               extent=[-0.15,1.05,0.25,2.75])
xs = np.array(bs); ys = np.array(sigmas)
cs = ax.contour(xs, ys, L, levels=[1.0], colors='k', linewidths=2.5)
ax.clabel(cs, fmt={1.0:'λ = 1 (idea R₀ criticality, theory)'}, fontsize=9)
for i,s_ in enumerate(sigmas):
    for j,b_ in enumerate(bs):
        ax.text(bs[j], sigmas[i], f"{D[i,j]:.0f}%", ha='center', va='center', fontsize=9,
                color='white' if D[i,j]>18 else 'black', fontweight='bold')
plt.colorbar(im, ax=ax, label='U-depth: discovery loss at full sharing (%)')
ax.set_xlabel('Lineage coupling b'); ax.set_ylabel('Noise σ/τ')
ax.set_title('C · Phase diagram: U appears where full deference makes\nthe idea branching process subcritical (λ<1)', fontsize=10.5, fontweight='bold')

# D) wrongful conviction rate: theory vs sim
ax = axes[1,1]
sig = [0.5,1.0,1.5,2.0,2.5]
WA = [0.042,0.067,0.083,0.094,0.103]
Wmix = [0.068,0.093,0.107,0.116,0.122]
WB = [0.535,0.377,0.296,0.256,0.232]
sim = [0.095,0.128,0.134,0.134,0.131]
ax.plot(sig, WA, 's--', color='#7f8c8d', label='theory: first-test failures $W_A$')
ax.plot(sig, Wmix, 'o-', color='#1a6fb4', lw=2, label='theory: all locks (2-channel mix)')
ax.plot(sig, sim, 'D', color='#d1495b', ms=8, label='simulation (pooled locks)')
ax.plot(sig, WB, '^:', color='#e8a628', label='theory: verification failures $W_B$')
ax.set_xlabel('Noise σ/τ'); ax.set_ylabel('P(idea is good | locked as dead)')
ax.set_title('D · Wrongful conviction rate: closed form tracks sim;\nnear-miss verdicts ($W_B$) are 30–50% wrong', fontsize=10.5, fontweight='bold')
ax.legend(fontsize=8.5)

fig.suptitle('Wrongful convictions in shared failure banks — sensitivity, phase structure, and theory', fontsize=13, fontweight='bold', y=1.0)
plt.tight_layout()
plt.savefig(_fig('deep_dive.png'), dpi=150, bbox_inches='tight')
print('saved')
