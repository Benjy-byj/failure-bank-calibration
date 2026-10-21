# Session Log

iter 1: E1 — Fourier + RK4, no dealiasing, dt=1e-4 → aliasing overflow at t=0.426 (before t=0.5), confirming BKdV-S1 prediction.
iter 2: E2 — Fourier + RK4 + 2/3 dealiasing (bug: products-only) → second blow-up at t=0.006 (modes 86-127 unstable, |dt*k_Nyq^3|=3.85>3.46); fixed by pre-dealiasing state in RHS → full run to T=6 with 15 peaks amp≥0.8, 0% mass drift, phenomenon target met.
