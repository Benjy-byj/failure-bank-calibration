import numpy as np, time
from scipy.special import ndtr

def run_once(rng, B, R, sigma, policy, s=None, k_strike=None, eps=None,
             mu0=-1.0, tau=1.0, mu0_hat=None, sigma_hat=None,
             v_verify=2, C=3, b=0.6, mu_c0=-0.27, anchor=0.55, tau_c=0.8, w=80):
    mu0_hat = mu0 if mu0_hat is None else mu0_hat
    sigma_hat = sigma if sigma_hat is None else sigma_hat
    cap = B*(1+C)+R+8
    delta = np.empty(cap); n_fail = np.zeros(cap, np.int32)
    locked = np.zeros(cap, bool); confirmed = np.zeros(cap, bool)
    sum_obs = np.zeros(cap); n_obs = np.zeros(cap, np.int32)
    delta[:R] = rng.normal(mu0, tau, R); N = R
    prec0 = 1.0/tau**2
    value=0.0; n_good=0; n_bad=0; t=0
    while t < B:
        alive = ~confirmed[:N]
        if policy in ('naive','kstrike'):
            idx = np.flatnonzero(alive & ~locked[:N])
            if idx.size==0 and policy=='kstrike':
                idx = np.array([],int)
        elif policy=='eps':
            vis = alive & (~locked[:N] | (rng.random(N) < eps))
            idx = np.flatnonzero(vis)
        else:  # calibrated with (possibly wrong) parameters
            pp = prec0 + n_obs[:N]/sigma_hat**2
            pm = (mu0_hat*prec0 + sum_obs[:N]/sigma_hat**2)/pp
            p_skip = np.where(n_fail[:N] > 0, ndtr(-pm*np.sqrt(pp)), 0.0)
            idx = np.flatnonzero(alive & (rng.random(N) >= p_skip))
            if idx.size==0:
                idx = np.flatnonzero(alive & (n_fail[:N] > 0))
        if idx.size==0: break
        k = idx[rng.integers(idx.size)]
        obs = delta[k] + rng.normal(0, sigma)
        sum_obs[k]+=obs; n_obs[k]+=1; t+=1
        if obs>0 and t<B:
            n_v = min(v_verify, B-t)
            ver = delta[k] + rng.normal(0, sigma, n_v)
            sum_obs[k]+=ver.sum(); n_obs[k]+=n_v; t+=n_v
            if (obs+ver.sum())/(1+n_v) > 0:
                confirmed[k]=True
                if delta[k]>0: value += delta[k]*(B-t)/B; n_good+=1
                else: value += delta[k]*min(w,B-t)/B; n_bad+=1
                delta[N:N+C] = rng.normal(mu_c0 + b*(delta[k]-anchor), tau_c, C); N+=C
                continue
        n_fail[k]+=1
        if policy=='naive' and rng.random()<s: locked[k]=True
        elif policy=='kstrike' and n_fail[k]>=k_strike: locked[k]=True
        elif policy=='eps': locked[k]=True
    return value, n_good, n_bad

def batch(reps, seed, **kw):
    rng = np.random.default_rng(seed)
    v = np.array([run_once(rng, **kw) for _ in range(reps)])
    return v.mean(0), v[:,1].std()/np.sqrt(reps)

B,R,sig = 800,80,1.5
configs = [
 ("fixed s=0.6 (naive best)", dict(policy='naive', s=0.6)),
 ("fixed s=1.0 (full bank)",  dict(policy='naive', s=1.0)),
 ("CAL oracle",               dict(policy='cal')),
 ("CAL sigma_hat=0.75 (2x under)", dict(policy='cal', sigma_hat=0.75)),
 ("CAL sigma_hat=3.0  (2x over)",  dict(policy='cal', sigma_hat=3.0)),
 ("CAL mu0_hat=-0.3 (optimist)",   dict(policy='cal', mu0_hat=-0.3)),
 ("CAL mu0_hat=-2.0 (pessimist)",  dict(policy='cal', mu0_hat=-2.0)),
 ("CAL both wrong (0.75,-2.0)",    dict(policy='cal', sigma_hat=0.75, mu0_hat=-2.0)),
 ("2-strikes",                dict(policy='kstrike', k_strike=2)),
 ("3-strikes",                dict(policy='kstrike', k_strike=3)),
 ("eps-revisit 0.05",         dict(policy='eps', eps=0.05)),
 ("eps-revisit 0.15",         dict(policy='eps', eps=0.15)),
]
print(f"== Robustness @ sigma={sig}, b=0.6, B={B}, reps=400 ==")
print(f"{'policy':34s}  good(se)      value   bad")
for name, kw in configs:
    m, se = batch(400, 11, B=B, R=R, sigma=sig, **kw)
    print(f"{name:34s}  {m[1]:5.1f}({se:.1f})   {m[0]:6.2f}  {m[2]:5.1f}")

print("\n== Budget check at the b=0.9 cliff ==")
for Bx in (400, 1600):
    for sg in (2.0, 2.5):
        gs=[]
        for s in (0,.3,.5,.7,.85,1.0):
            m,_ = batch(200, 13, B=Bx, R=80, sigma=sg, policy='naive', s=s, b=0.9)
            gs.append(m[1])
        gs=np.array(gs)
        print(f"B={Bx:4d} sigma={sg}: U-depth={(gs.max()-gs[-1])/gs.max()*100:5.1f}%  (goods: {np.round(gs,1)})")

print("\n== Anchor stress (b=0.6, sigma=1.5) ==")
for anc in (0.3, 0.55, 0.8):
    gs=[]
    for s in (0,.3,.5,.7,.85,1.0):
        m,_ = batch(200, 17, B=800, R=80, sigma=1.5, policy='naive', s=s, anchor=anc)
        gs.append(m[1])
    gs=np.array(gs)
    print(f"anchor={anc}: U-depth={(gs.max()-gs[-1])/gs.max()*100:5.1f}%  peak={gs.max():.1f}  (goods: {np.round(gs,1)})")
