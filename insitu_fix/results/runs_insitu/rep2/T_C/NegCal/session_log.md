# Session log — T_C NegCal

iter 1: baseline Fourier+2/3-dealias+RK4, no u-dissipation, dt=2e-4 — bore Gibbs blow-up: u_max=10.26>>5, TV=796; v_max=0.677 (passes) but u fails
iter 2: added linear u-viscosity nu=5e-2 (single upgrade, BKdV-S6 recommendation) — success: final v_max=0.5055>=0.5 (single soliton peak at x=10.78), u_max=1.398<5, TV_u=6.5; stop early
