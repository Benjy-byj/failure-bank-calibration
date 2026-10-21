# Session Log — T_A NegOnly

iter 1: Fourier+2/3-dealias+RK4 at dt=2e-4 with suggested IC (m=0.2v); soliton decays from v_max=2.0 to 0.635 at T=8 (31.8% retention, 4 peaks, all-finite) — fails amplitude target >=1.0.
iter 2: Reduced IC perturbation to 0.02*v; v_max(T=8)=0.701 (marginal improvement from 0.635). IC perturbation change alone insufficient since u growth is driven by -d_x(3v^2) coupling (IC-independent).
iter 3: E3=E1 (removing post-step dealiasing makes zero difference; pre-RHS dealiasing fully controls dynamics). Best result is E2 (v_max=0.701, mass 0%, bounded). Rolling back to E2 output as final.
