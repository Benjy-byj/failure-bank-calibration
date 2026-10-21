# Session Log

iter 1: Fourier pseudospectral + classical RK4 + 2/3-rule dealiasing, dt=2e-4, Nx=256, Gaussian IC v0=4*exp(-(x+5)^2/2.25), u0=0, T=6.0 — baseline solver following BKdV-S1 validated stack. Bug-fix during same iteration: dispersive term must use dealiased v_hat (modes |k_idx|>85 would otherwise have dt*k^3>2.83, exceeding RK4 stability). Result: 13 peaks with amplitude >= 0.8, 0% mass drift — phenomenon target met, early stop.
