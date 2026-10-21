# Reasoning — T_C Burgers bore × KdV soliton

## Final method

**E3**: Fourier pseudospectral + explicit RK4 + 2/3-rule spectral dealiasing + linear viscosity nu=1e-2 on u-equation only.

Full description:
- Domain: x ∈ [-15, 15] (L=30), Nx=256, dt=2e-4, T=8.0, 10 snapshots
- Spatial: Fourier spectral derivatives for all terms (u_x, v_x, v_xxx)
- Dealiasing: 2/3-rule (zero Fourier modes with |k_idx| > Nx/3 = 85)
- Time: classical 4-stage Runge-Kutta (RK4)
- u-RHS modification: add nu*u_xx = ifft(-nu*k^2*fft_dealiased(u)) with nu=1e-2
- v-RHS: standard (no viscosity on v)
- All nonlinear products (u*u_x, v*v_x, u_x*v, u*v_x) computed in physical space and dealiased before summing into the RHS

Stability: viscous CFL = nu*k_eff^2*dt = 0.0006 << 1 (explicit stability is fine).

## Iteration trace

**E1** (Fourier+RK4, no dealiasing, dt=2e-4): blew up at t=0.0028, step 14 from aliasing overflow in quadratic products (v^2, u*v, v*v_x). One snapshot saved (IC only). Exact failure mode predicted by BKdV-S1.

**E2** (Fourier+RK4+2/3 dealias, no u-viscosity, dt=2e-4): ran to T=8 without NaN. Dealiasing fixed the aliasing blow-up (BKdV-S1). However, Burgers bore-steepening without u-side dissipation caused: u_max=3.206 (2.1x IC), u_min=-1.55 (negative bore), TV(u)=202 (42x). v_max=0.718 with 4 spurious peaks from coupling to corrupted u field. Confirms BKdV-S6 bore-inflation failure mode.

**E3** (Fourier+RK4+2/3 dealias+nu=1e-2 u-viscosity, dt=2e-4): all phenomenon targets met. u stays bounded and positive (u_max=1.632<5, u_min=0.097>0). TV(u)=22.28 (9x improvement over E2). Soliton survived: v_max=0.595>=0.5. Bore-soliton interaction visible: v_max drops from 1.499 to 0.526 during crossing at t≈2.67, then recovers to 0.595 at T=8.

## Use of memory

- **BKdV-S1** (negative, deep synthesis): confirmed that Fourier+RK4 without 2/3 dealiasing blows up before t=0.5 on this exact amplitude regime. Used at E1 to predict the expected failure mode, and at E2 to select the single-component fix (add 2/3 dealiasing).
- **BKdV-S6** (negative, deep synthesis): directly matched this IC — bore u0=1.5*(1-tanh(x/0.5))/2 + soliton v0=1.5*sech^2(x+5). Predicted u_max grows 2.3x and TV(u) grows 42x without u-side viscosity; recommended nu_lin=1e-2 as minimum sufficient value. Applied at E3 to select the single-component upgrade.

Considered but rejected:
- **kb-kdv-explicit-RK4-stiffness-blowup**: warns of soliton fragmentation from explicit v_xxx. Did not trigger because 2/3 dealiasing reduces k_max_eff to (2/3)*26.8=17.9, making RK4 stable at dt=2e-4 (CFL bound ~4.9e-4). Not a binding constraint at our parameters.
- **kb-gardner-sech2IC-not-exact-soliton**: warns IC v=A*sech^2(x+x0) is not exact KdV/Gardner soliton. True, but for this task the IC is prescribed; some radiation is expected and acceptable as the threshold is v_max>=0.5 (not exact amplitude preservation).
- **BKdV-S6 hyperviscosity route**: nu_h<=1e-10 fails on bore IC; only nu_h=1e-9 at RK4 stability ceiling passes. Chosen linear viscosity nu=1e-2 instead (simpler and safer per bank recommendation).

## Final self-assessment

`pred_results/T_C.npy` satisfies the phenomenon target with confidence:

1. **v_max = 0.595 >= 0.5** (soliton survived): The primary peak of v at T=8 has amplitude 0.595. During the bore-crossing at t≈2.67, v_max dropped to 0.526 (still above 0.5), then recovered. The soliton transmitted through the bore with ~40% amplitude retention (1.499 → 0.595).

2. **|u_max| = 1.632 < 5** (u bounded): The bore amplitude at T=8 is 1.632, below the IC value of 1.5... actually slightly above because viscosity was not strong enough to prevent all transient amplification, but well below the threshold of 5.

3. **Bore not blown up**: u stays positive throughout (u_min=0.097 at T=8), indicating the bore structure is physically intact. TV(u)=22.28 is elevated but not catastrophically so.

4. **10 snapshots** cover the full time interval [0, 8], showing the complete bore-soliton encounter.

The interaction appears to be **partial transmission/refraction**: the soliton crosses the bore with amplitude reduction (~40% retained), consistent with the known behavior of KdV-type solitons encountering an amplitude step.
