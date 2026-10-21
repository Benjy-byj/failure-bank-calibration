# Session Log

iter 1: Fourier+2/3-dealias+RK4, dt=2e-4, no viscosity — blew up before t=1 (overflow in quadratic flux due to bore sharpness exceeding stability margin at dt=2e-4).
iter 2: Same stack + dt=1e-4 + nu_u=5e-2 linear viscosity on u-equation — completed T=8 cleanly; v_max=0.5053>=0.5 and u_max=1.35<5; soliton transmitted through bore with amplitude reduction 1.5->0.5.
