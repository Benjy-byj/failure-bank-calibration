# Reasoning — T_C: Burgers Bore–KdV Soliton Interaction

## Final method

**Experiment E3**: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + linear viscosity nu=5e-2 on u-equation.

- **Spatial**: Fourier pseudospectral derivatives on x∈[-15,15], Nx=256
- **Time**: Classical RK4, dt=1e-4, 80000 steps (T=8)
- **Dealiasing**: 2/3-rule (zero modes |k_idx| > Nx/3 = 85) applied to all nonlinear products (u*u_x, v*v_x, v^2, u*v)
- **u-viscosity**: nu*u_xx with nu=5e-2, treated explicitly in RK4 (stable: nu*k_max^2*dt ~ 3.6e-3 << 2.79)
- **v-equation**: no viscosity; dispersive term v_xxx treated fully explicitly
- **Output**: 9 snapshots at t=0,1,...,8, shape (9,2,256)

## Iteration trace

1. **E1** (Fourier+RK4, no dealiasing): Blow-up at t=0.76 from aliasing overflow in v^2 product. Confirmed BKdV-S1 deep synthesis prediction.

2. **E2** (add 2/3 dealiasing, no viscosity): No NaN blow-up. Reached T=8. But bore over-steepened severely: u_min=-1.356 (negative, physically corrupt), TV(u) inflated, v_max at t=6 = 0.469 (below 0.5 threshold), v_max at T=8 = 0.867 (suspicious recovery via bore-oscillation contamination of v). Confirmed BKdV-S6 failure mode.

3. **E3** (add nu=5e-2 viscosity on u): Bore controlled: u stays positive from t=6 onward (u_min_final=0.164), u_max_final=1.45 < 5. Soliton v weakens during bore interaction (t=3-7: v_max 0.41-0.50) then recovers to v_max=0.5052 at T=8. 3 peaks at T=8 (transmitted soliton + dispersive radiation). Mass conserved to machine precision throughout.

## Use of memory

**Cited entries:**
- **BKdV-S1** (deep synthesis): Confirmed that 2/3-rule dealiasing is the minimal fix for aliasing blow-up; working stack Fourier+2/3+RK4 at dt≤2e-4 is confirmed. Directed single-component upgrade for E2.
- **BKdV-S6** (deep synthesis + individual entries): EXACT match to our bore IC (u=1.5*(1-tanh(x/0.5))/2). Confirmed that without u-viscosity, bore steepens to 2.3x u_max and TV inflates 42x even with dealiasing. Recommended nu_linear=5e-2 as the empirically validated minimum. This entry directly drove E3's single component change.

**Rejected entries:**
- **BKdV-S1 no-dealiasing route**: ruled out for E2+ (aliasing confirmed in E1)
- **kb-burgers-fwdEuler-centralFD-Gibbs**, **kb-general-centralFD-hyperbolic-shockFormation**: no central FD used (spectral throughout)
- **kb-burgers-LaxFriedrichs-longTime-dissipation**: not applicable (using spectral, not Lax-Friedrichs)
- **BKdV-S6 no-viscosity bore route**: confirmed as failure in F2, then applied its fix in E3

## Final self-assessment

**pred_results/T_C.npy** (shape 9,2,256) from E3:
- `v_max at T=8 = 0.5052 >= 0.5` ✓ (soliton survived)
- `u_max_final = 1.4484 < 5` ✓ (bore bounded)
- `|u_min_final| = 0.164 > 0` ✓ (bore physically positive, not blown up)
- `mass_v = 3.0000` at all snapshots (machine-precision conservation)
- All values finite throughout

The phenomenon target criteria are nominally met. The soliton amplitude margin is tight (0.5052 vs threshold 0.5). The soliton undergoes a multi-traversal interaction with the bore on the periodic domain (soliton phase speed ~9 units/t, domain 30 units, T=8 → roughly 2.4 traversals) and emerges with reduced but surviving amplitude. Physics interpretation: soliton transmission/refraction through the bore with energy loss to dispersive radiation.

**Risk**: v_max=0.5052 is only 1% above the 0.5 threshold. If the parent evaluator uses slightly stricter criteria or checks intermediate times (v_max dips to 0.418 at t=4), the result could be marginal. The viscosity nu=5e-2 is necessary to stabilize the bore but also reduces soliton-bore coupling energy.
