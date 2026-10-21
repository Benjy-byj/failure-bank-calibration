# Session Log

iter 1: E1 — Fourier+2/3-dealias+RK4 (no viscosity), dt=2e-4; initial run blew up at step 17 due to missing pre-dealiasing of u,v before v_xxx computation; bug fixed (pre-dealias state at each RHS call), rerun completed T=8 cleanly with v_max=0.61, u_max=4.17, all 9 snapshots finite.
iter 2: E2 — same stack + nu_lin=5e-2 on u (BKdV-S6 recommendation); u_max reduced to 1.44 (cleaner bore) but v_max dropped to 0.42 at t=4 and only recovered to 0.505 at T=8 (worse than E1's minimum 0.517); rolled back to E1 as final answer.
