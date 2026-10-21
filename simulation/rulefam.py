import numpy as np
from scipy.special import ndtr

def run_once(rng, B, R, sigma, rule, param,
             mu0=-1.0, tau=1.0, v_verify=2, C=3, b=0.6, mu_c0=-0.27, anchor=0.55, tau_c=0.8, w=80):
    cap = B*(1+C)+R+8
    delta=np.empty(cap); n_fail=np.zeros(cap,np.int32)
    confirmed=np.zeros(cap,bool); sum_obs=np.zeros(cap); n_obs=np.zeros(cap,np.int32)
    delta[:R]=rng.normal(mu0,tau,R); N=R
    prec0=1.0/tau**2; value=0.0; n_good=0; n_bad=0; t=0
    while t<B:
        alive=~confirmed[:N]
        pp=prec0+n_obs[:N]/sigma**2
        pm=(mu0*prec0+sum_obs[:N]/sigma**2)/pp
        p_dead=ndtr(-pm*np.sqrt(pp))
        if rule=='power':      p_skip=p_dead**param
        elif rule=='thresh':   p_skip=(p_dead>param).astype(float)
        elif rule=='thresh_parole': p_skip=np.where(p_dead>param, 0.97, 0.0)
        p_skip=np.where(n_fail[:N]>0, p_skip, 0.0)
        idx=np.flatnonzero(alive & (rng.random(N)>=p_skip))
        if idx.size==0:
            idx=np.flatnonzero(alive & (n_fail[:N]>0))
            if idx.size==0: break
        k=idx[rng.integers(idx.size)]
        obs=delta[k]+rng.normal(0,sigma); sum_obs[k]+=obs; n_obs[k]+=1; t+=1
        if obs>0 and t<B:
            n_v=min(v_verify,B-t); ver=delta[k]+rng.normal(0,sigma,n_v)
            sum_obs[k]+=ver.sum(); n_obs[k]+=n_v; t+=n_v
            if (obs+ver.sum())/(1+n_v)>0:
                confirmed[k]=True
                if delta[k]>0: value+=delta[k]*(B-t)/B; n_good+=1
                else: value+=delta[k]*min(w,B-t)/B; n_bad+=1
                delta[N:N+C]=rng.normal(mu_c0+b*(delta[k]-anchor),tau_c,C); N+=C
                continue
        n_fail[k]+=1
    return value,n_good,n_bad

def batch(rule,param,reps=400,seed=31):
    rng=np.random.default_rng(seed)
    v=np.array([run_once(rng,800,80,1.5,rule,param) for _ in range(reps)])
    return v[:,1].mean(), v[:,1].std()/np.sqrt(reps)

print("rule                 good(se)   [sigma=1.5, b=0.6, B=800; prob-matching = power k=1 = oracle CAL]")
for k in (0.15,0.25,0.5,1.0,2.0):
    g,se=batch('power',k); print(f"power k={k:<5}        {g:5.1f}({se:.1f})   skip=p_dead^{k}")
for th in (0.5,0.65,0.8,0.9,0.97):
    g,se=batch('thresh',th); print(f"threshold {th:<5}      {g:5.1f}({se:.1f})   hard-lock iff p_dead>{th}")
for th in (0.65,0.8,0.9):
    g,se=batch('thresh_parole',th); print(f"thresh {th}+parole3%  {g:5.1f}({se:.1f})")
