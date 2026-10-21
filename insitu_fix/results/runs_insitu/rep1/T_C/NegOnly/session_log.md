# Session Log

iter 1: Fourier+RK4 no-dealiasing baseline blew up at t=0.76 from aliasing overflow (confirmed BKdV-S1 prediction)
iter 2: Added 2/3-rule dealiasing; no NaN blow-up but bore over-steepened (u_min=-1.356 negative, v_max dips to 0.469 at t=6, confirmed BKdV-S6 failure mode)
iter 3: Added linear viscosity nu=5e-2 on u; bore stays physical (u_min=0.164, u_max=1.45<5), soliton survives with v_max=0.5052 at T=8 (above 0.5 threshold)
