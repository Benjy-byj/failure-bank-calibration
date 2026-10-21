# Session Log

iter 1: Fourier pseudospectral + 2/3-rule dealiasing + RK4, pre-dealiased v for dispersive term (effective k_eff=17.8), dt=2e-4 — BLEW UP (first attempt with full v_hat); BUG FIX used pre-dealiased vd_hat; result: v_max=0.635 at T=8, all-finite, mass conserved, but 4 peaks and amplitude below threshold.
iter 2: Same method, full v_hat for dispersive term, dt=1e-4 (within RK4 stability at k_max=26.84) — identical result to iter 1: v_max=0.635, confirms numerical convergence; physics is determined by IC shape, not discretization.
iter 3: Same method as E2, but epsilon reduced from 0.2 to 0.05 in IC (u=0.5v^2+0.05v) — v_max=0.653 at T=8 (marginally better), same rapid initial drop; confirms sech^2 IC radiates energy for coupled BKdV regardless of perturbation size.
