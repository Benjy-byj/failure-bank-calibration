# Session Log — T_B NegCal

iter 1: Fourier+2/3-dealias+RK4 baseline (E1, dt=2e-4): produced 14 v-peaks with min separation 1.4 units and TV(u)=654 (Burgers shock in u from u0=0 forced by v coupling), corrupting v into spurious multi-peak state.
iter 2: Added linear viscosity nu_u=0.05 to u equation only (E2, single-component change): TV(u) dropped to 24.8, u bounded to ±1.5; v shows 5 well-separated peaks all >=0.8 amplitude (min 0.84, min sep 3.16 units), mass(v) drift=0%; phenomenon target met — stopping early.
