# Session Log

iter 1: E1 (Fourier+RK4, no dealias, dt=2e-4) blew up at t=0.0028 step 14 — aliasing cascade confirmed as in BKdV-S1.
iter 2: E2 (Fourier+RK4+2/3 dealias, no u-viscosity, dt=2e-4) reached T=8 but u corrupted: u_max=3.2, u_min=-1.55, TV=202; v_max=0.718 with 4 peaks — BKdV-S6 bore-inflation confirmed.
iter 3: E3 (Fourier+RK4+2/3 dealias+nu=1e-2 u-viscosity, dt=2e-4) all targets met: v_max=0.595>=0.5, u_max=1.632<5, TV(u)=22.28; soliton transmitted through bore with ~40% amplitude retention. STOP early.
