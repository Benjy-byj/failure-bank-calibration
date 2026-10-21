# Session Log

iter 1: Fourier-pseudospectral + explicit RK4, dt=1e-4; blew up at t≈0.4 (NaN in v before t=0.889 snapshot) due to aliasing/instability from quadratic coupling terms.
iter 2: Added 2/3-rule dealiasing (single-component change); simulation ran to T=8 successfully; v_max(T=8)=0.665>=0.5, max|u|=3.64<5, v_mean conserved at 0.1. Early stop — phenomenon targets met.
