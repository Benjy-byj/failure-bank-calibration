# Reasoning — Soliton Stability in Coupled Burgers-swept-KdV

## Final method

**E3** is the final solver (also identical in method to E2, with slightly adjusted IC):

- **Spatial**: Fourier pseudospectral, Nx=256, domain [-15,15] (L=30)
- **Time**: Explicit RK4, dt=1e-4
- **Dealiasing**: 2/3-rule (zeroing modes |k_idx| > 85 = Nx/3) applied to ALL nonlinear products (u·u_x, v·v_x, u·v), but NOT to the linear dispersive term
- **Dispersive term**: full v_hat used for ik^3·v_hat in both u- and v-equations; stability satisfied: dt·k_max^3 = 1e-4 × 26.84^3 = 1.93 < 2.83 (RK4 stability threshold)
- **IC**: v(x,0) = 2·sech^2(x+5), u(x,0) = 0.5·v^2 + 0.05·v (epsilon=0.05, "close to v^2/2")
- **Output**: 10 snapshots, t ∈ [0, 8], shape (10, 2, 256)

PDE implementation (Fourier space):
```
û_t = -3·dealias(FFT(u·u_x)) - 6·dealias(FFT(v·v_x)) + ik^3·v_hat
v̂_t = -6·dealias(FFT(v·v_x)) + ik^3·v_hat - ik·dealias(FFT(u·v))
```

## Iteration trace

**E1 / F1**: Fourier+2/3+RK4, pre-dealiased vd_hat for dispersive term, dt=2e-4. First attempt (full v_hat) blew up at t≈0.89 (dt too large for k_max^3 stability); bug-fixed by pre-dealiasing. Result: v_max=0.635, 4 peaks, mass conserved exactly, all finite. Fails amplitude target (< 1.0). Convergence check: need full v_hat at dt=1e-4.

**E2 / F2**: Same method, full v_hat for dispersive term (standard pseudospectral), dt=1e-4. Result: v_max=0.635 to 5 decimal places — **identical to E1**. Confirms solution is numerically converged; failure is physical, not numerical. The soliton at T=3.56 still has v_max=1.09 (above threshold) but decays to 0.635 by T=8.

**E3 / F3**: Same method as E2, but IC with epsilon=0.05 instead of 0.2 (smaller perturbation from Gardner reduction). Result: v_max=0.653 — marginally higher but still below 1.0. Identical rapid initial drop (2.0→1.60 by t=0.89) in all three runs. Three experiments converge: the sech^2 IC shape drives radiation independently of perturbation size.

## Use of memory

**Used / cited**:
- `BKdV-S1` (CLOSED synthesis): directly guided choice of Fourier+2/3-rule+RK4+dt≤2e-4 as the validated working stack for the BKdV coupled system at amp≤3. Also explained the blow-up mechanism at first attempt (missing/wrong k^3·v_hat stability). Provided the dt=2e-4 baseline from which we escalated to dt=1e-4 to use full v_hat safely.
- `kb-kdv-noDealiasing-aliasing-artifacts` (OPEN): reinforced mandatory 2/3 dealiasing — without it aliasing inflates amplitude and creates spurious peaks.
- `kb-burgers-fwdEuler-centralFD-Gibbs` (CLOSED): ruled out central FD → use spectral from the start.
- `kb-gardner-sech2IC-not-exact-soliton` (CLOSED): directly predicted the observed rapid initial drop — sech^2 ICs radiate energy in Gardner (and BKdV coupled) systems because the KdV soliton shape is not the exact soliton for this PDE. Explains why even at epsilon→0 the soliton decays.

**Considered but rejected**:
- `kb-kdv-IFRK4-blowup` (OPEN): warned about IFRK4 implementation pitfalls; chose explicit RK4 (simpler, validated by BKdV-S1) instead. IF-RK4 would not change the physical result (E1=E2 convergence confirmed).
- `kb-gardner-GardnerIsM0-coupledSystemInstability` (OPEN): warns Gardner instability carries into coupled system; considered but our result already shows this — the instability is physical, not numerical.
- `BKdV-S7` deep synthesis: predicted sech^2 IC at A≥1 leads to fragmentation/radiation in coupled BKdV. Confirmed by our observations (identical rapid drop across all experiments). The bank correctly predicted the failure mode.

## Final self-assessment

**pred_results/T_A.npy** corresponds to E3 (best run).

| Criterion | Target | E3 Result | Pass? |
|-----------|--------|-----------|-------|
| v_final max (amplitude) | ≥ 1.0 | 0.653 | **FAIL** |
| mass(v) drift | < 8% | 0.000% | ✓ |
| \|max(u)\| < 15 | < 15 | 5.88 | ✓ |
| \|max(v)\| < 15 | < 15 | 0.653 | ✓ |
| Single dominant peak | yes | yes (ratio 3.7:1) | ✓ |
| All finite | yes | yes | ✓ |

**The soliton structure partially survives**: there is a single clearly-dominant peak (v_max=0.653, next peak=0.177, ratio 3.7:1), mass is exactly conserved (0% drift), and fields are fully bounded. However, the amplitude retention is only 32.6% (threshold 50%).

**Physical interpretation**: The sech^2 IC is not an exact soliton of the coupled BKdV system (consistent with bank entry kb-gardner-sech2IC-not-exact-soliton CLOSED). The initial condition immediately radiates energy, causing the v_max to drop from 2.0 to ~1.60 within the first t=0.89 time unit. After this transient, the dominant peak persists but decays slowly. Three experiments with different discretizations and IC perturbation magnitudes (epsilon=0.2 and epsilon=0.05) all converge to the same physics: v_max≈0.65 at T=8. The soliton survives as a recognizable structure but loses ~67% of its amplitude by T=8 due to radiation and coupling with the growing u field (u_max grows from 2.09 to 5.88).

**Confidence**: High confidence this is the correct physical result for the given system. The numerical method (Fourier+2/3+RK4) is validated by BKdV-S1 at amp≤3, dt and discretization are converged (E1=E2 to 5 decimal places), and the epsilon variation (E2→E3) confirms robustness with respect to IC perturbation magnitude.
