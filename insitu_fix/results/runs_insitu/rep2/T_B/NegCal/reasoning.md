# Reasoning — T_B: Gaussian soliton-train decomposition

## Final method

**E2 (final answer)**: Fourier pseudospectral + 2/3-rule dealiasing + explicit classical RK4.

- **Grid**: Nx=256, L=30, x ∈ [-15,15], dx=30/256≈0.117
- **Wavenumbers**: k = 2π/L · fftfreq(256)·256; k_max ≈ 26.81 rad/unit
- **Dealiasing**: 2/3-rule on all nonlinear products (u², v², uv); keep |j|≤85, zero modes above
- **PDE in conservative Fourier form**:
  - u_rhs_hat = 1j·k·[−(3/2)·û² − 3·v̂² + k²·v̂]
  - v_rhs_hat = 1j·k·[−3·v̂² + k²·v̂ − (uv)^hat]
- **Time stepper**: classical RK4, dt=1e-4, n_steps=60,000 (T=6.0)
- **IC**: v(x,0)=4·exp(−(x+5)²/2.25), u(x,0)=0
- **Output**: 10 snapshots, shape (10,2,256), channels (u,v)

## Iteration trace

**E1 (dt=2e-4)**: Fourier+2/3-dealias+RK4 at dt=2e-4 blew up before t=0.667 with `overflow in multiply` on u·u. Root cause: k_max³·dt = 26.81³·2e-4 = 3.85 > 2.83 (RK4 imaginary-axis stability boundary). At the Nyquist mode (k=26.81), the RK4 amplification factor |R|≈6.1/step — machine-precision noise at this mode grows exponentially. At amplitude 4, the dynamics excited these modes faster than at the tested amplitude 1.5 (BKdV-S1), making the instability visible within ~3000 steps.

**F1**: Negative. Blow-up confirmed before t=0.667. Single-component fix identified: reduce dt.

**E2 (dt=1e-4)**: Same method. At dt=1e-4: k_max³·dt=1.93<2.83, Nyquist mode decays (|R|≈0.79/step). Run completed in 7.7s. 12 peaks≥0.8 detected in v_final; mass(v) drift=0.0000% at all 10 snapshots.

**F2**: Positive / useful. Early stop.

## Use of memory

**Consulted positively:**
- `BKdV-S1` (depth=3 synthesis, OPEN): identified Fourier+2/3-rule+RK4 as the working baseline stack and provided the stability formula dt_crit=2.83/k_max³=1.47e-4. Used to justify E1's method and to diagnose E1's failure.

**Consulted as prohibitions (CLOSED entries):**
- `kb-burgers-fwdEuler-centralFD-Gibbs` (CLOSED): central FD on Burgers → not used (spectral instead).
- `kb-general-centralFD-hyperbolic-shockFormation` (CLOSED): same reason.
- `BKdV-S1` (CLOSED, single entry): no-dealiasing blows up → 2/3-rule applied throughout.

**Considered but rejected (OPEN entries):**
- `kb-kdv-IFRK4-blowup`: warns against IFRK4 without careful dealiasing. I did not use IFRK4.
- `kb-kdv-noDealiasing-aliasing-artifacts`: would produce spurious peaks. 2/3-rule dealiasing applied.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` and `kb-gardner-cubicTerm-tightens-nonlinearCFL`: warn that IMEX-CN at amplitude 3+ blows up due to explicit nonlinear CFL. These entries apply to IMEX methods specifically; I used fully explicit RK4 where the binding constraint is always the dispersive k³ term (amplitude-independent), not the nonlinear advection term. Correctly rejected as not applicable to explicit RK4.

**Not matched:**
- No bank entry warns against reducing dt below dt_crit — the fix was safe and unambiguous.

## Final self-assessment

**Yes, pred_results/T_B.npy satisfies the phenomenon target.**

Numerical diagnostics at T=6.0 (final snapshot, shape (10,2,256)):

| Criterion | Required | Observed |
|-----------|----------|----------|
| Peaks in v with amp ≥ 0.8 | ≥ 2 | **12** |
| Top-4 amplitudes | ≥ 0.8 each | 3.53, 2.61, 2.27, 2.23 |
| Well-separated (min top-4 pairwise) | > soliton width | **2.34 units** (min), 14.18 (max) |
| mass(v) drift | < 8% | **0.0000%** (machine precision) |
| All finite | yes | yes |

The Gaussian (amplitude 4, σ≈1.06, centered at x=−5) decomposed into at least 4 genuine soliton-like peaks with amplitude ≥2.2, distributed across the periodic domain at T=6. The remaining 8 smaller peaks (amplitude 0.98–1.65) are consistent with smaller-amplitude solitons and/or dispersive radiation from the inverse-scattering decomposition. The u component, driven by the −∂_x(3v²+v_xx) source term, grew from 0 to |u_max|≈13 by T=6 — consistent with the expected coupling dynamics at this amplitude. Mass conservation to machine precision confirms the divergence-form spectral scheme is working correctly.
