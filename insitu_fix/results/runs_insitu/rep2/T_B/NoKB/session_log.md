iter 1: Fourier pseudospectral + explicit RK4 (no dealiasing, dt=1e-4) — blew up at t=0.5 (aliasing-driven Burgers shock in u; v was fine)
iter 2: Added 2/3-rule dealiasing to E1 — blow-up delayed to t=0.6 but Burgers shock in u (u_max -> 15 -> inf) persists; halving dt confirmed near-physical singularity
iter 3: Replaced spectral Burgers derivative for u with conservative TVD-MUSCL (minmod + Rusanov flux) — ran to T=6 stably; 7 peaks >= 0.8 in v at T=6, mass drift 0.00%; phenomenon target met
