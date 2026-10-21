import json, time, numpy as np
from sim_core import sweep_s
from scipy.stats import multivariate_normal as mvn
from scipy.special import ndtr

# ---- Phase diagram over (sigma, b) ----
import os
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
def _p(name, where=None):
    """Resolve a data file from the repo root, so scripts run from any directory."""
    return str((_ROOT / where / name) if where else (_HERE / name))
B, R = 800, 80
s6 = (0, .3, .5, .7, .85, 1.0)
sigmas = (0.5, 1.0, 1.5, 2.0, 2.5)
bs = (0.0, 0.3, 0.6, 0.9)
phase = {}
t0 = time.time()
for sig in sigmas:
    for b in bs:
        rows, cal = sweep_s(B, R, sig, s6, reps=220, seed=7, b=b)
        phase[f"{sig}|{b}"] = {'rows': rows.tolist(), 'cal': cal.tolist()}
    print(f"sigma={sig} done {time.time()-t0:.0f}s", flush=True)
json.dump(phase, open(_p('phase.json'),'w'))

# ---- Theory: closed-form wrongful conviction probability ----
# delta ~ N(mu0, tau^2); obs = delta + eps, eps ~ N(0, sigma^2)
# W = P(delta > 0 | obs <= 0)  via bivariate normal orthant
def W_theory(mu0, tau, sigma):
    v = np.sqrt(tau**2 + sigma**2); rho = tau / v
    # P(delta>0, obs<=0) = P(Z1 > -mu0/tau, Z2 <= -mu0/v), corr(Z1,Z2)=rho
    z1, z2 = -mu0/tau, -mu0/v
    p_joint = mvn(mean=[0,0], cov=[[1,-rho],[-rho,1]]).cdf([-z1, z2])  # P(Z1>z1, Z2<=z2)=P(-Z1<-z1,Z2<=z2)
    return p_joint / ndtr(z2)

print("\nsigma | W_theory(first-obs) | sim wrongful/locks (b=0.6, pooled over s>0)")
for sig in sigmas:
    rows = np.array(phase[f"{sig}|0.6"]['rows'])
    wl, lk = rows[1:,5].sum(), rows[1:,6].sum()   # skip s=0 (no locks)
    print(f"{sig:4.1f} |  {W_theory(-1,1,sig):.3f}            |  {wl/lk:.3f}")

# ---- U-depth table ----
print("\nU-depth (right drop = (peak-s1)/peak of good count):")
print("        " + "".join(f"b={b:<6}" for b in bs))
for sig in sigmas:
    line = f"sig={sig:<4}"
    for b in bs:
        r = np.array(phase[f"{sig}|{b}"]['rows']); g = r[:,2]
        line += f"{(g.max()-g[-1])/g.max()*100:5.1f}%  "
    print(line)
print("\nleft rise = (peak-s0)/peak:")
for sig in sigmas:
    line = f"sig={sig:<4}"
    for b in bs:
        r = np.array(phase[f"{sig}|{b}"]['rows']); g = r[:,2]
        line += f"{(g.max()-g[0])/g.max()*100:5.1f}%  "
    print(line)
