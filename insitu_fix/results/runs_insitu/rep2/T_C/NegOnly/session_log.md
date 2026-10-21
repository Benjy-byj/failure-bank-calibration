# Session Log

iter 1: Fourier+2/3-dealias+RK4 baseline (no u-viscosity), dt=2e-4 — bore steepens (TV=160, u_max=4.17), v_max=0.607 borderline, bore Gibbs blow-up in accuracy
iter 2: Added nu_u=5e-2 linear viscosity on u_xx (BKdV-S6 recommendation) — bore clean (TV=7, u_max=1.44) but v_max barely 0.505 (over-diffuses soliton indirectly)
iter 3: Reduced nu_u to 1e-2 (BKdV-S6 minimum sufficient) — bore controlled (TV=21, u_max=1.71), v_max=0.595 comfortably above 0.5, all phenomenon targets met
