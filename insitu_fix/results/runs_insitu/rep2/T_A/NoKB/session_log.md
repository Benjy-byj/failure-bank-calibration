iter 1: E1 — pseudospectral RK4 dt=1e-4 no dealiasing; blowup at t=0.65 from aliasing instability (high-k energy grew 4 orders of magnitude before NaN).
iter 2: E2 — added 2/3-rule dealiasing; stable to T=8; peak v=0.635 at T=8, mass drift=0.00%, single soliton tracked across periodic domain; amplitude below 1.0 threshold.
iter 3: E3 — rewrote nonlinear terms in conservation form (single d/dx of flux); bit-identical to E2, confirming amplitude decay is physical (radiation from ε=0.2 perturbation) not numerical.
