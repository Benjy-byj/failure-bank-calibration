iter 1: E1 (Fourier+2/3-dealias+RK4, dt=2e-4, no u-viscosity) blew up at t=0.0076 — dt too large for bore IC's steep gradient without dissipation.
iter 2: E2 (same but dt=1e-4) survived to T=8 but u_max=9.74 (fails |u_max|<5 target) and TV(u)=733 — bore Gibbs catastrophe without u-side dissipation.
iter 3: E3 (add nu=5e-2 linear viscosity on u-equation) passed both targets: v_max=0.5053>=0.5 and |u_max|=1.39<5; soliton survived interaction with bore with partial amplitude recovery.
