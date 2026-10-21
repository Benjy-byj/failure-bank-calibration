# Session Log

iter 1: E1 Fourier+RK4 no-dealiasing blew up at t=1.04 via aliasing overflow of quadratic products (confirmed BKdV-S1 failure mode)
iter 2: E2 Fourier+RK4+2/3-dealias (no viscosity) completed T=8 but bore blown up (TV=235, u_min=-2.23); 5 v peaks; nominal targets met but physically incorrect
iter 3: E3 added nu_u=5e-2 linear viscosity on u; clean result: v_max=0.505 (single peak at x=10.8), u_max=1.34, TV(u)=5; soliton transmitted through bore; all phenomenon targets met
