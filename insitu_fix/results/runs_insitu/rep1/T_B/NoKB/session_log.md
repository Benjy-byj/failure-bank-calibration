# Session Log

iter 1: E1 — pseudospectral RK4, no dealiasing; blew up at t=0.6 (step 6000) with overflow in nonlinear multiply, NaN propagation — aliasing instability.
iter 2: E2 — added 2/3-rule dealiasing to E1; ran to T=6.0 successfully with 12 soliton peaks (amplitude≥0.8), 0.00% mass drift — phenomenon target met, early stop.
