# Session Log

iter 1: E1 — Fourier pseudospectral + RK4, no dealiasing — aliasing overflow at t=2.5 (NaN)
iter 2: E2 — added 2/3-rule dealiasing — survived to T=8 but 79 Gibbs-ringing peaks in v, v_max=0.68
iter 3: E3 — Hou-Li exponential filter every step — over-dissipative (v_max=0.37); self-rollback to E2-refined (2/3 dealiasing on nonlinear, full spectrum on linear v_xxx) — v_max=0.635, 9 coherent peaks, mass drift 0%, both bounded
