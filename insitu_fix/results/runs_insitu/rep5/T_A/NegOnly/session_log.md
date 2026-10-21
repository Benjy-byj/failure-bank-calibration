# Session log

iter 1: Fourier+RK4, no dealiasing — blew up at step 20 (t=0.004) from aliasing overflow in u*v products, confirming BKdV-S1 deep synthesis prediction.
iter 2: Added 2/3-rule dealiasing (single component change) — stable to T=8, but v_max=0.635 (34% retention) below 1.0 threshold; u grew to u_max=6.03 draining the soliton via strong Burgers dynamics from large u0=v0^2/2+0.2*v0.
iter 3: Changed IC to u0=0.2*v0 (u0_max=0.4 vs 2.4; removes dominant v0^2/2 term) — stable to T=8, mass drift=0.00%, but v_max=0.68 (34% retention) still below 1.0; A^2-scaled coupling at A=2.0 is 2.8x stronger than BKdV-S3's tested range, causing faster soliton fragmentation.
