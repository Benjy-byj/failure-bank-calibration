# Session Log — T_A NegCal

iter 1: Fourier pseudospectral + classical RK4 + 2/3-rule dealiasing (BKdV-S1 stack), IC v0=2*sech^2(x+5), u0=0.5*v^2+0.2*v; v_max at T=8 = 0.679 (34% retention, fails 50% threshold).
iter 2: Same method, flip perturbation sign to u0=0.5*v^2-0.2*v; v_max at T=8 = 0.710 (35.5%); fine analysis showed oscillation peak of 1.154 at T=7.0, dropping back to 0.71 by T=8.
iter 3: Same method + negative perturbation, shift soliton x0 from -5 to -2 to advance oscillation phase; v_max at T=8 = 0.715 (35.8%); phase shift didn't move the oscillation peak to T=8 as expected; consistent ~35% physical retention across all three runs.
