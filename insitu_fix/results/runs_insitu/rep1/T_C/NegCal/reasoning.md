# Reasoning — T_C: Burgers bore interacting with KdV soliton

## Final method

**E3: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (fully explicit) + linear viscosity nu_u=1e-2 on u-equation.**

Parameters: Nx=256, L=30, dt=1e-4, nu_u=1e-2, T=8.0, 9 snapshots at t=0,1,...,8.

PDE implemented:
- u_t = -3/2 * ∂_x(u^2) - 3 * ∂_x(v^2) - v_xxx + nu_u * u_xx
- v_t = -3 * ∂_x(v^2) - v_xxx - ∂_x(u*v)

All nonlinear products (u^2, v^2, u*v) are dealiased with the 2/3-rule (zero modes with |k_idx| > Nx/3 = 85). Linear terms (v_xxx, u_xx) are computed on the full spectrum.

## Iteration trace

- **E1 / F1 (negative)**: Fourier+2/3-dealias+RK4, dt=2e-4, no viscosity. Immediate blow-up at step 18 (t=0.0036). Cause: CFL violation on v_xxx term. Explicit RK4 stability requires dt < 2.83/k_max^3 ~ 1.47e-4; dt=2e-4 violates this.

- **E2 / F2 (partial)**: Fixed dt=1e-4 (now below CFL limit) + added nu_u=5e-2 linear viscosity on u-equation (per BKdV-S6 recommendation for bore ICs). Ran to T=8 without blow-up: u_max=1.34<5, v_max=0.506>=0.5 (barely passing). Soliton transmitted through bore. Criterion met but margin thin.

- **E3 / F3 (positive)**: Reduced nu_u from 5e-2 to 1e-2 (minimum sufficient per BKdV-S6). Better result: v_max=0.607 (comfortable margin above 0.5), u_max=1.69<5, no blow-up. Three v-peaks at T=8 (x≈7.85, 10.90, 14.41), all to the right of the bore. EARLY STOP.

## Use of memory

**Used:**
- `BKdV-S1` (deep synthesis): Confirmed that Fourier+2/3+RK4 is the validated working stack for BKdV at amp in [1,3]. Informed E1/E2/E3 baseline architecture.
- `BKdV-S4`: Warning about dispersion CFL dt <= 2.83/k_max^3 from v_xxx term in u-equation. Explained the E1 blow-up and motivated dt=1e-4 in E2/E3.
- `BKdV-S6` (deep synthesis + 3 entries): Critical for bore IC. No viscosity → u_max 2.3x, TV 42x. Recommended nu_lin=5e-2 as default. nu=1e-2 (minimum sufficient) tried in E3 with better soliton amplitude preservation.

**Considered but not used:**
- `kb-general-centralFD-hyperbolic-shockFormation` (CLOSED): Rejected central FD entirely — using Fourier spectral.
- `kb-kdv-noDealiasing-aliasing-artifacts`: Rejected no-dealiasing — using 2/3-rule.
- `kb-gardner-sech2IC-not-exact-soliton` (CLOSED): This is for Gardner equation specifically. Our v-equation is KdV-type, and the sech^2 IC is approximately correct (not exact, but close enough for KdV solitons).
- `BKdV-S1` no-dealiasing entry (CLOSED): Avoided — using 2/3 dealiasing.

## Final self-assessment

**pred_results/T_C.npy satisfies the phenomenon target.**

Numerical diagnostics at T=8.0 (E3 result):
- v_max = 0.607 >= 0.5 ✓ (soliton survived with comfortable margin)
- u_max = 1.693 < 5 ✓ (bore bounded)
- All values finite ✓ (np.isfinite check passed)
- 9 snapshots (t=0,1,2,3,4,5,6,7,8) capture bore-soliton encounter ✓
- mass_v conserved to 6 decimal places ✓

**Physics observed**: The KdV soliton (starting at x=-8, amplitude 1.5) traveled rightward, encountered the bore (centered at x=0) around t=2-3. During the interaction (t=3-6), v_max dipped to 0.46-0.56. After the interaction, the soliton transmitted through the bore and appears in the region x>7 at T=8, with 3 peaks (possibly soliton + dispersive radiation). The bore decayed from u_max=2.83 at t=2 to 1.69 at T=8 due to linear viscosity.
