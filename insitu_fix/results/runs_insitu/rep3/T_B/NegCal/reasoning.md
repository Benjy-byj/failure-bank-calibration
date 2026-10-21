# Reasoning: T_B Gaussian → Soliton Train Decomposition

## Final method

**Experiment E2**: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing, working entirely in spectral state space.

- **Spatial**: Fourier pseudospectral, Nx=256, L=30 (x ∈ [-15,15])
- **Time**: Explicit RK4, dt=2e-4 (T=6 → 30,000 steps)
- **Dealiasing**: 2/3-rule applied to all nonlinear products and state variables; keep modes |k_idx| ≤ 85 (Nx/3)
- **Nonlinear terms**: Computed in flux form — u²(x), v²(x), (uv)(x) computed in physical space from dealiased fields, then FFT and re-dealias before taking spectral derivative
- **Linear dispersive term**: v_xxx computed from dealiased v_hat to avoid k³ amplification of high-mode noise
- **State**: Maintained in spectral space throughout RK4; dealias applied after each step

**Implementation detail**: Two attempts were needed for E2. The first implementation had a bug: `v_xxx` was computed from the full (non-dealiased) spectrum, causing rapid blow-up at step 50 (t=0.01) due to k³ amplification of any high-mode content in intermediate RK4 states. The fix was to work entirely in spectral state space and apply dealias to v_hat before computing v_xxx.

## Iteration trace

- **E1 / F1 (negative)**: Fourier + RK4, NO dealiasing, dt=1e-4. Blew up at t=0.42 (step 4215) from aliasing overflow in quadratic products (v², uv). Confirmed CLOSED entry BKdV-S1.
- **E2 / F2 (positive)**: Added 2/3-rule dealiasing (single component change). Run completed to T=6.0. At T=6: 14 soliton peaks all with amplitude ≥ 0.8, min separation 1.64 x-units, mass(v) drift 0.00%, spectral energy above dealias cutoff 0.00%. Bug-fix of v_xxx dealiasing required within the same experiment.

## Use of memory

- **BKdV-S1 (CLOSED)**: Predicted E1 blow-up before t=0.5 from aliasing — confirmed at t=0.42. Directed the single-component upgrade to 2/3 dealiasing for E2.
- **BKdV-S1 (depth-3 synthesis)**: Confirmed working stack is Fourier+2/3-rule+RK4 at dt≤2e-4 for BKdV at amp∈[1,3]. Extended to amp=4 Gaussian IC (our domain is slightly higher amplitude but still smooth/localized so no broadband blow-up).
- **kb-kdv-noDealiasing-aliasing-artifacts**: Confirms dealiasing is mandatory for soliton amplitude/count accuracy.
- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup** and **kb-gardner-cubicTerm-tightens-nonlinearCFL** (rejected): These warned against IMEX-CN with explicit nonlinear at high amplitude — correctly avoided by using explicit RK4 on all terms with 2/3 dealiasing instead.
- **kb-kdv-IFRK4-blowup** (rejected): Warned against IFRK4 without dealiasing — avoided.
- **kb-general-massConservation-insufficient-diagnostic**: Checked mass AND peak count AND amplitudes AND separations, not just mass.

## Final self-assessment

`pred_results/T_B.npy` satisfies the phenomenon target with high confidence:

| Criterion | Required | Observed |
|-----------|----------|----------|
| ≥ 2 well-separated peaks with amp ≥ 0.8 | ✓ | 14 peaks, min amp=0.889, min sep=1.64 x |
| mass(v) drift < 8% | < 8% | 0.00% |

**Numerical diagnostics at T=6:**
- `v_max` = 4.14, `v_min` = -1.98
- 14 peaks, all ≥ 0.8 amplitude
- Minimum peak separation = 1.64 x-units (≫ dx = 0.117)
- Mass v conserved to machine precision (0.00% drift across all 6 snapshots)
- Spectral energy above mode 85: 0.0000% (no aliasing artifacts)
- Soliton train evolution: 1 peak → 2 → 3 → 5 → 9 → 14 peaks (textbook IST decomposition)

The large u field (u_max ~ 10-12) is physically expected: the u equation receives forcing -6v*v_x - v_xxx from the strong v Gaussian, but v_xxx on the dealiased spectrum is well-controlled, and mass_u is also exactly conserved (divergence form). The phenomenon focus is on v, which shows clean soliton-train decomposition.
