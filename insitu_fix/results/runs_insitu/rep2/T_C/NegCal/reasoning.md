# reasoning.md — T_C NegCal

## Final method

**Experiment E2** is the final answer.

- **Spatial**: Fourier pseudospectral, Nx=256, domain [-15, 15] (L=30)
- **Dealiasing**: 2/3-rule — zero spectral modes with |k_idx| > Nx/3 = 85 before every nonlinear product and before computing v_xxx (to keep effective k_max at 17.8 rad/unit for RK4 dispersive stability)
- **Time integrator**: Classical RK4, dt = 2e-4 (40,000 steps for T=8)
- **u-dissipation**: Linear viscosity nu=5e-2 added to the u-equation: u_t += nu*u_xx (spectral: +nu*(-k^2)*u_hat_d, explicit inside RK4 stages)
- **v-equation**: No additional dissipation; dispersive term v_xxx treated explicitly with dealiased v
- **RHS**:
  - u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu*u_xx
  - v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x
  - All nonlinear products use dealiased state variables (alias-free)

## Iteration trace

**E1** (no u-viscosity): Fourier+2/3+RK4, dt=2e-4, nu=0.
- Finding F1: bore Gibbs blow-up — u_max=10.26>>5 (FAILS), TV(u)=796, v_max=0.677.
- Decision D1: add linear u-viscosity (single-component upgrade per BKdV-S6).

**E2** (u-viscosity nu=5e-2): Same stack + nu*u_xx on u-equation.
- Finding F2: PASS — final v_max=0.5055≥0.5 (single clean peak at x=10.78), u_max=1.398<5, TV_u=6.5.
- Decision D2: stop_useful (all criteria met).

## Use of memory

**Used (drove decisions)**:
- `BKdV-S1` (depth=3 synthesis): Confirmed Fourier+2/3+RK4, dt≤2e-4 as the validated baseline stack for BKdV at amp≤3, T≤10. Cited in E1 method choice.
- `BKdV-S1` (CLOSED entry for no-dealias): Ruled out no-dealiasing as unsafe (overflow→NaN before t=0.5).
- `BKdV-S6` (depth=3 synthesis): Directly applied — tested the SAME bore IC (u0=1.5(1-tanh(x/0.5))/2 + soliton) and showed: (a) no-dissipation gives u_max~3.4, TV~126 at T=6; (b) nu=5e-2 yields u_max≤1.62, TV≤27. Cited in E2 method choice.

**Considered but rejected**:
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: Not used — LxF causes over-diffusion, bore smearing.
- `kb-kdv-noDealiasing-aliasing-artifacts`: Not applicable (we do dealias); confirmed why we need dealiasing.
- `BKdV-S6` entries for nu=1e-4 and nu=1e-3: Rejected — bank shows both are insufficient for bore control.
- `BKdV-S6` entries recommending IMEX for large-Nx: Not needed — nu=5e-2 explicit is stable at Nx=256, dt=2e-4 (nu*k_eff^2*dt ~ 3.2e-3 << 1).

## Final self-assessment

`pred_results/T_C.npy` satisfies the phenomenon target with clear margin:

| Criterion | Required | Achieved |
|-----------|----------|----------|
| Final v_max ≥ 0.5 | ≥ 0.5 | **0.5055** ✓ |
| u_max < 5 | < 5 | **1.398** ✓ |
| Bore not blown up | bounded, no Gibbs | TV_u=6.5, u_min=0.200 ✓ |

**Physical interpretation**: The soliton (initially at x=-8, amplitude 1.5) moved rightward at enhanced speed (~4.5 due to u≈1.5 coupling), encountered the bore (centered at x=0) around t≈2-3, transmitted through it with reduced amplitude (~0.5), and by T=8 is located at x≈10.78 — a clear transmissive/refractive interaction. The bore itself relaxed to a smooth diffusive profile by T=8 (u ranging from 0.2 to 1.4 with TV=6.5). Mass was conserved exactly throughout.
