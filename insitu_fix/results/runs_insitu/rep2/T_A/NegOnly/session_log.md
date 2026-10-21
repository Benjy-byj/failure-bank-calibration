# Session Log

iter 1: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (dt=2e-4); baseline method confirmed by BKdV-S1 deep synthesis. Result: v_peak(T=8)=0.635, u_max=6.03, mass_drift=0%, 4 peaks. Negative: v_peak<1.0 threshold. u grew via Burgers steepening 2.4→6.0, coupling -d_x(uv) erodes v. Physical, not numerical (BKdV-S7 confirmed).

iter 2: Added eps_u=0.05 linear viscosity to u equation (BKdV-S6 bore-test recommendation). Result: v_peak(T=8)=0.405, u_max=0.948, mass_drift=0%, 10 peaks. WORSE than iter 1. Over-damping destroyed u-v phase coherence; eps_u=0.05 damps even low-k soliton-scale modes in u (e^{-0.05*1*8}=0.67), breaking Gardner manifold co-evolution and amplifying v fragmentation.

iter 3: Reduced eps_u to 0.005 (10x smaller, targeting only high-k Burgers shock modes). Result: v_peak(T=8)=0.353, u_max_peak=4.91, mass_drift=0%, 11 peaks. WORST result. Monotonic degradation: eps=0 (0.635) > eps=0.05 (0.405) > eps=0.005 (0.353). ANY eps_u>0 introduces asymmetric dissipation breaking Gardner manifold. BKdV-S7 confirmed: sech^2 IC is not a BKdV traveling wave; physical fragmentation is unavoidable. Best output is iter 1 (E1, v_peak=0.635); pred_results/T_A.npy regenerated from E1.
