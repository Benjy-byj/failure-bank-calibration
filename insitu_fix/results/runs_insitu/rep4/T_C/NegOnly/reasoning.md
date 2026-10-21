# Reasoning — T_C: Burgers bore interacting with KdV soliton

## Final method

**Experiment E2** (selected as the final answer):
- Fourier pseudospectral, Nx=256, domain [-15, 15] (L=30), periodic
- 2/3-rule dealiasing on all nonlinear products (zero modes with |k_idx| > Nx/3 = 85)
- Classical 4th-order Runge-Kutta (RK4), fully explicit
- dt = 1e-4 (80,000 steps for T=8)
- Linear viscosity nu_u = 5e-2 on u-equation only: u-RHS += nu_u * u_xx (spectral: -nu_u * k^2 * u_hat)
- No viscosity on v-equation

**PDE formulation in Fourier space:**
```
u_hat_t = +ik^3 * v_hat - ik * fft(3*u_d^2/2 + 3*v_d^2) - nu_u * k^2 * u_hat
v_hat_t = +ik^3 * v_hat - ik * fft(3*v_d^2 + u_d * v_d)
```
where subscript _d denotes 2/3-dealiased physical fields.

**Stability checks:**
- Dispersive CFL (RK4 on +ik^3): dt * k_max^3 = 1e-4 * 17.87^3 = 0.57 < 2.83 ✓
- Advective CFL (3*u_max * dt / dx): 3 * 1.5 * 1e-4 / 0.117 = 3.8e-3 ✓
- Viscous CFL: nu_u * k_max^2 * dt = 5e-2 * 17.87^2 * 1e-4 = 1.6e-3 ✓

## Iteration trace

**E1** (Fourier+2/3-dealias+RK4, dt=2e-4, nu_u=0):
Blow-up before t=1 with overflow in u_d^2 flux. The smoothed bore (transition width 0.5) generates high-k energy during Burgers steepening that exceeds the stability margin at dt=2e-4 (BKdV-S6 used dt=1e-4 for the same bore IC).

**E2** (Fourier+2/3-dealias+RK4, dt=1e-4, nu_u=5e-2):
Completed T=8 cleanly. Soliton trajectory: x=-7.97 at t=0 → x=10.78 at t=8, amplitude 1.5→0.50. Bore stayed bounded (u_max=1.35, u_min=0.17>0). All 9 snapshots finite.

## Use of memory

**Used:**
- `BKdV-S1` (deep synthesis): Confirmed Fourier+2/3-rule+RK4 is the baseline working stack. Established dt<=2e-4 is safe for smooth soliton ICs (but not for the steep bore IC here).
- `BKdV-S6` (deep synthesis, E1+E3): **Primary guide.** Exact IC match (same bore u0, same soliton amplitude). Recommended nu_linear=5e-2 as default for bore-like ICs. Confirmed dt=1e-4 as the stable timestep. E3 sweep showed nu>=1e-2 passes TV and u_max bounds.

**Considered but rejected:**
- `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-general-centralFD-hyperbolic-shockFormation`: Ruled out central FD for any hyperbolic component — used spectral with dealiasing instead.
- `kb-kdv-noDealiasing-aliasing-artifacts`, `kb-gardner-G3-noDealiasing-cubicAliasing`: Confirmed 2/3 dealiasing is mandatory; applied throughout.
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: Ruled out LxF (over-diffusive for T=8 runs).
- `BKdV-S6 (eps=1e-4 case)`: Bank explicitly shows nu=1e-4 is insufficient (7% improvement over no-viscosity). Used nu=5e-2 directly.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: Considered IMEX for v_xxx but explicit RK4 with 2/3 dealiasing is stable at dt=1e-4 (k_max^3 * dt = 0.57 < 2.83), so IMEX not needed.

## Final self-assessment

**Phenomenon target satisfied:**
- v_max at T=8 = **0.5053** >= 0.5 ✓ (soliton survived as recognizable peak at x=10.78)
- |u_max| at T=8 = **1.35** < 5 ✓
- Bore not blown up: u_min = 0.17 > 0, no Gibbs oscillations ✓
- All 9 snapshots finite ✓
- Output shape (9, 2, 256) ✓

**Physical interpretation:**
The soliton (amplitude 1.5 at x=-8) traveled right at approximately speed 2.3-3, encountered the bore near x=0 at t≈2.5, was partially transmitted through the bore with amplitude reduction to ~0.4-0.5 during interaction (t=2-4), then continued rightward. At T=8, the dominant v-peak is at x=10.78 with amplitude 0.5053. Secondary peaks at x=7.27 (0.33) and x=14.65 (0.13) represent dispersive radiation shed during the interaction. The behavior is consistent with **soliton transmission (refraction)** through the bore: the soliton survived but with reduced amplitude and phase shift.
