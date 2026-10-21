# Reasoning — T_A: Soliton Stability in Coupled Burgers-swept-KdV

## Final method

**E1 / E3 (converged): Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4, dt=2e-4, Nx=256, L=30, T=8.**

PDE solved:
- `u_t = -3*u*u_x - 6*v*v_x - v_xxx`
- `v_t = -6*v*v_x - v_xxx - (u*v)_x`

Key implementation detail: the 2/3-rule mask is applied to **both** `u_hat` and `v_hat` at the **start** of every `rhs()` call. This zeroes modes with `|k| > (2/3)*(Nx/2)*(2*pi/L) = 17.87 rad/m`. Without this, modes 86–127 receive a k^3 amplification factor with `dt*k_nyq^3 = 3.85 > 2.83` (RK4 stability limit on the imaginary axis) and blow up explosively by step ~20.

Nonlinear products (uu_x, vv_x, u*v) computed from dealiased physical fields; (u*v)_x takes the spectral derivative of the product with the mask applied before differentiation.

## Iteration trace

| Iter | Experiment | Outcome |
|------|-----------|---------|
| E1   | Fourier+2/3+RK4, dt=2e-4 (initial: blew up; fixed by masking v_hat fully) | v_peak=0.635 at T=8, u grew to 7.5, mass drift 0.00% |
| E2   | E1 + nu_u=0.02 viscosity on u-equation | v_peak=0.395 (worse); viscosity dissipates energy exchange channel |
| E3   | E1 method with dt=5e-5 (4x smaller) | v_peak=0.635 — **identical to E1** → dt convergence confirmed |

## Use of memory

**Used:**
- `BKdV-S1` (synthesis): confirmed Fourier+2/3+RK4 at dt≤2e-4 is the validated working stack for BKdV at amp≤3, T=10. Guided E1 baseline choice.
- `BKdV-S6` (synthesis): identified that Burgers steepening drives u to large amplitude; recommended linear viscosity nu_lin≥1e-2 on u-equation → tested in E2.

**Considered but rejected:**
- `kb-kdv-IFRK4-blowup` (OPEN): advisory against IFRK4 without dealiasing — not relevant since we used RK4 without IF.
- `kb-gardner-sech2IC-not-exact-soliton` (CLOSED): warns that sech^2 IC in Gardner is not the exact soliton. Relevant — our IC IS a KdV soliton shape but NOT the Gardner soliton, which explains some of the amplitude decay. However, since the task prescribes this IC, we used it as specified.
- `BKdV-S7` (synthesis): predicts Gardner manifold (m=0) is not BKdV-invariant → consistent with our observation that soliton decays.
- `kb-general-centralFD-hyperbolic-shockFormation` (CLOSED): confirms spectral method is required for hyperbolic terms — already satisfied by Fourier pseudospectral.

**Bank gap:** no positive bank entries were available (NegOnly condition), so escalation direction relied solely on negative-entry guidance and first-principles analysis.

## Final self-assessment

**pred_results/T_A.npy shape:** (8, 2, 256) — 8 snapshots at t = 0, 8/7, 16/7, ..., 8.

**Numerical diagnostics at T=8:**
- `v_final peak = 0.6351` — single **dominant** peak (ratio 3.3× vs 2nd largest peak of 0.195)
- `mass(v) drift = 0.00%` — passes < 8% criterion
- `u_max = 7.517` — passes < 15 bound
- `v_max = 0.635` — passes < 15 bound
- No NaN/Inf

**Amplitude criterion (>= 1.0):** NOT met. The converged physical result shows v retention of 31.8% at T=8.

**Physical interpretation:** The sech^2 IC (v0=2*sech^2) is the KdV soliton shape but NOT the exact Burgers-swept-KdV soliton. Starting off the Gardner manifold by m=0.2*v causes:
1. Immediate energy exchange between u and v via coupling terms
2. u steepens (Burgers: 3*u*u_x) growing 2.4→7.5 → strong -d_x(u*v) forcing on v
3. Soliton partially survives as single dominant peak until t~3.5, then disperses

The soliton IS coherent (dominant:second = 3.3:1) but amplitude fails the ≥1.0 criterion. dt convergence (E1=E3 to 4 decimal places) confirms this is the correct physical answer for the specified IC and PDE.
