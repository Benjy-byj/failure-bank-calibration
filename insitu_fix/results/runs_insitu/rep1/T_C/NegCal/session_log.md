# Session Log

iter 1: E1 (Fourier+2/3-dealias+RK4, dt=2e-4, no viscosity) blew up at step 18 (t=0.0036) due to CFL violation on v_xxx (dt>dt_crit~1.47e-4).
iter 2: E2 (same + dt=1e-4 + nu_u=5e-2 linear viscosity) completed to T=8: v_max=0.506 (marginal, barely >= 0.5), u_max=1.34.
iter 3: E3 (same as E2 but nu_u=1e-2) completed to T=8: v_max=0.607 (clear margin), u_max=1.69, bore bounded. Phenomenon target met. Early stop.
