# Reasoning — T_B: Gaussian wave packet → soliton train decomposition

## Final method

**E1 (only experiment executed)**:
- Spatial discretization: Fourier pseudospectral on periodic domain x ∈ [-15,15], Nx=256
- Dealiasing: 2/3-rule (zero modes with |k_index| > Nx/3 = 85) applied to every nonlinear product before summing into the RHS
- Time integrator: classical RK4, fully explicit (no IMEX, no integrating factor)
- dt = 1e-4, n_steps = 60 000

**PDE handled**:
```
u_t = -3*u*u_x  -  6*v*v_x  -  v_xxx
v_t = -6*v*v_x  -  v_xxx  -  (u*v)_x
```
Both nonlinear products (u·u_x, v·v_x, u·v) are dealiased in spectral space after multiplication in physical space.

## Iteration trace

| Iter | Method | Finding |
|------|--------|---------|
| E1 | Fourier + 2/3 dealiasing + RK4, dt=1e-4 | Positive: 12 prominent peaks (height≥0.8, prominence≥0.5) at T=6, mass drift=0%, all finite. Early stop. |

## Use of memory

**Cited**:
- `BKdV-S1` (deep synthesis): The validated working stack for coupled BKdV is Fourier + 2/3-rule + classical RK4 at dt≤2e-4. I directly adopted this for E1, choosing dt=1e-4 (more conservative) due to the higher amplitude A=4 (vs validated A≤3).

**Rejected / not used**:
- `kb-kdv-IFRK4-blowup`: Rejected integrating-factor approach — complex implementation, overflow at high k without careful dealiasing.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` + `kb-gardner-nonlinearCFL-amplitude-boundary`: Rejected IMEX-CN because at A=4 the nonlinear CFL for explicit nonlinear component is max|6v+1.5v²|=48, about 4× larger than validated A=1.5 (12.4), making IMEX blow-up likely. Using fully explicit RK4 avoids this amplitude-dependent constraint.
- `kb-kdv-noDealiasing-aliasing-artifacts` + `kb-gardner-G3-noDealiasing-cubicAliasing`: Confirmed dealiasing mandatory; 2/3-rule applied.
- `BKdV-S6` (bore IC): Warns about u-side dissipation for steep bore ICs. Not applicable here because u(x,0)=0; no pre-existing bore.
- `kb-burgers-fwdEuler-centralFD-Gibbs` + `kb-general-centralFD-hyperbolic-shockFormation`: Confirmed Fourier spectral (not FD) is appropriate.

## Final self-assessment

**`pred_results/T_B.npy` satisfies the phenomenon target.**

Numerical evidence:
- **all_finite = True** — no NaN or Inf in any snapshot
- **12 prominent peaks** with height ≥ 0.8 and prominence ≥ 0.5 at T=6, far exceeding the required ≥2
  - Peak amplitudes: 3.51, 2.58, 1.74, 2.48, 1.87, 1.89, 1.53, 2.25, 1.39, 1.25, 0.89, 0.95
  - Peak locations span x ∈ [-14.6, 11.8], well-distributed across the domain
- **mass(v) drift = 0.0000%** (spectral divergence-form conservation to machine precision) — far below the 8% threshold
- The Gaussian IC (A=4, centered at x=−5) decomposed by T=6 into a rich soliton-like multi-peak train consistent with KdV inverse-scattering decomposition
