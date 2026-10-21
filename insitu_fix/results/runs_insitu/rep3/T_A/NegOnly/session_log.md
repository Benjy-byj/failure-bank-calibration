# Session Log

iter 1: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4, dt=2e-4, Nx=256 — baseline from BKdV-S1 deep synthesis; gives 31.8% retention, 4 peaks at T=8 (FAILS amplitude criterion)
iter 2: Same IC, upgraded to Cox-Matthews IFRK4 (integrating factor for v_xxx) — gives identical 31.8% retention; fragmentation is PHYSICAL not numerical
iter 3: Reduced IC perturbation epsilon=0.02 (from 0.2), kept IFRK4 — modest improvement to 35.2% retention (0.703 amplitude); dominant single peak maintained, mass drift 0.13%, bounded; fails 50% amplitude threshold
