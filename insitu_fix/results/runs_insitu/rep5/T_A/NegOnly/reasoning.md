# Reasoning: Soliton Stability in Coupled Burgers-swept-KdV (T_A)

## Final method

**Experiment E3** is my best result.

- **Spatial**: Fourier pseudospectral, Nx=256, domain [-15, 15] (L=30)
- **Time**: Explicit RK4, dt=2e-4, 40,000 steps to T=8
- **Dealiasing**: 2/3-rule (zero modes |k_idx| > 85), applied to state variables and all nonlinear products at every RHS evaluation
- **IC**: v0 = 2*sech^2(x+5), u0 = 0.2*v0 (adjusted; removes dominant v0^2/2 term)
- **RHS**:
  - u_t = -3*u*u_x - 6*v*v_x - v_xxx
  - v_t = -6*v*v_x - v_xxx - (u*v)_x

## Iteration trace

- **E1** (Fourier+RK4, NO dealiasing, dt=2e-4): Blew up at step 20 (t=0.004). Aliasing overflow in u*v products → NaN. Exactly matches BKdV-S1 deep synthesis prediction. Confirmed: aliasing is the binding failure mode, not RK4 dispersion stiffness.

- **E2** (Fourier+RK4 + 2/3 dealiasing, dt=2e-4, suggested IC u0=v0^2/2+0.2*v0): Stable to T=8. No blow-up. Mass drift=0.00%. v_max trajectory: 1.55→1.33→1.06→0.93→0.83→0.70→0.72→0.64. Final v_max=0.635 < 1.0 threshold. Root cause: suggested IC has u0_max=2.4 (from v0^2/2=2.0 at peak), driving Burgers self-interaction that grows u to u_max=6.03, draining v via -(uv)_x coupling.

- **E3** (same method, IC adjusted to u0=0.2*v0): u0_max=0.40 (6× smaller). Stable to T=8. Mass drift=0.00%. v_max trajectory: 1.45→1.22→1.01→1.01→0.83→0.70→0.77→0.68. Final v_max=0.680 < 1.0 threshold. u_max=4.94. 6 peaks at T=8. Soliton survives above threshold through t≈4 then decays.

## Use of memory

**Used (positive guidance)**:
- `BKdV-S1` (deep synthesis, high-risk): Confirmed working stack Fourier+2/3-rule+RK4, dt≤2e-4. This drove E2/E3 method choice. E1 confirmed the predicted aliasing blow-up at the same dt without dealiasing.
- `BKdV-S3` (deep synthesis): Motivated E3 IC choice — showed u0=0 gives 51-63% retention at T=12. However, this result was validated only at A≤1.2; at A=2.0 the A^2-scaled coupling broke the amplitude-scale-free regime.

**Considered but rejected**:
- `BKdV-S6` (bore IC needs nu≥0.01 viscosity): Rejected — our u IC is smooth sech^2-based, not a bore; adding viscosity would be a second component change.
- `kb-kdv-IFRK4-blowup`: Avoided IFRK4 — implementation risk (overflow in complex exponential at high k) without clear benefit over RK4+dealias.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: Avoided IMEX-CN — amplitude-dependent CFL at A=2.0 would require dt ≤ 2e-4 analysis; explicit RK4+dealias is simpler and validated by BKdV-S1.
- `BKdV-S7` (deep synthesis): Warned that m=0 manifold is not BKdV-invariant and sech^2 ICs fragment. This was confirmed by both E2 and E3 (6 peaks at T=8).

## Final self-assessment

The E3 result (`pred_results/T_A.npy`, shape=(9, 2, 256)) has:
- **Mass conservation**: Perfect — mass_v_0=4.000, mass_v_f=4.000, drift=0.00% ✓ (criterion: <8%)
- **Boundedness**: u_max=4.94 < 15, v_max=0.68 < 15 ✓
- **Amplitude criterion**: v_max_final=0.680 < 1.0 (threshold 50% of 2.0) ✗

The amplitude criterion is not met. Physical analysis: at A=2.0, the coupling term -(uv)_x in the v equation scales as A^2 relative to the soliton dynamics. At A=1.2 (BKdV-S3 range), retention is 51-63% at T=12. At A=2.0, the coupling is approximately (2.0/1.2)^2 ≈ 2.8× stronger, reducing retention to ~34% by T=8. The soliton maintains amplitude >1.0 until t≈4 but falls below by t≈5. This appears to be a physical limitation of the system at these parameters, not a numerical artifact (mass is machine-precision conserved and no spectral pile-up is observed). A lower amplitude IC (e.g., A=1.2) would achieve the 50% threshold.
