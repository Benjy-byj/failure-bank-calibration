# Session Log

iter 1: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (dt=2e-4) — baseline per BKdV-S1 bank; v_max=0.678 at T=8 (fails amplitude criterion of 1.0)
iter 2: Same method, dt reduced 4x to 5e-5 — byte-identical output to E1; confirms result is time-converged physics not numerics
iter 3: Added u-side linear viscosity nu_u=5e-3 — v_max dropped further to 0.361 (worse); u-viscosity removes coupling that partially sustains v
