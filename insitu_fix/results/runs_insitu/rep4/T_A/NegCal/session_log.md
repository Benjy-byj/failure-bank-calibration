# Session Log

iter 1: Fourier+2/3-dealias+RK4 (dt=2e-4) — blew up at step 41 due to full-spectrum v_xxx instability (dt*k_nyq^3=3.85>2.83); fixed by masking v_hat at rhs entry; rerun gave stable result v_peak=0.635 at T=8 (below 1.0 criterion, u grew 2.4→7.5).
iter 2: Added linear viscosity nu_u=0.02 on u-equation (BKdV-S6 recommendation) — counterproductive: v_peak declined to 0.395; viscosity dissipates energy channel sustaining v.
iter 3: E1 method with dt=5e-5 (4x reduction) — IDENTICAL result (v_peak=0.635, u_max=7.517); confirms dt convergence, amplitude decay is physical not numerical.
