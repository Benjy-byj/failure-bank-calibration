# Session Log

iter 1: Fourier+2/3+RK4 dt=2e-4, KdV sech^2 IC: v_peak decays 1.997→0.678 at T=8 (retention 34%), fails v>=1.0 target; soliton fragments due to BKdV-S7 physics (not numerical).
iter 2: Gardner soliton IC + m=0.2v (E2): v_peak=0.662 at T=8, similar retention to E1 (33.2%); Gardner soliton spectral content 99.99% below 2/3 cutoff, confirming no dealiasing artifact.
iter 3: Gardner soliton IC + m=0 (exact Gardner manifold, E3): v_peak=0.782 at T=8 (best result, 39.2% retention); all criteria except v_peak>=1.0 satisfied; physical fragmentation confirmed.
