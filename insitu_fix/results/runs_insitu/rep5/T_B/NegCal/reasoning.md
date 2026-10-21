# Reasoning — T_B: Gaussian Wave Packet → Soliton Train Decomposition

## Final method

**Experiment E1**: Fourier pseudospectral spatial discretization + classical RK4 time integration (fully explicit, no IMEX) + 2/3-rule dealiasing on all nonlinear products.

- Domain: x ∈ [-15, 15], L = 30, Nx = 256
- Time step: dt = 2e-4, n_steps = 30000 (T = 6.0)
- IC: v(x, 0) = 4·exp(−(x+5)²/2.25), u(x, 0) = 0
- Dealiasing: zero modes with |k_idx| > Nx/3 = 85 in all nonlinear products AND in the dispersive term
- After each RK4 step: project back to dealiased subspace

**Critical implementation detail**: the dispersive term ik³·v̂ must use the _dealiased_ v̂ (not full v̂). For modes |k_idx| > 85, the wavenumber satisfies k > 2π×85/30 ≈ 17.8 and dt×k³ > 2e-4×(26.8)³ ≈ 3.85 > 2.83, exceeding the RK4 stability boundary for imaginary eigenvalues. Using the full v̂ caused blow-up at t ≈ 0.6 (first attempted run). Using the dealiased v̂ (effective k_max ≈ 17.8) gives dt×k_max³ ≈ 1.13 < 2.83: stable.

## Iteration trace

**E1 / F1** (iter 1, early stop):
- Fourier+2/3+RK4, dt=2e-4, IC as above. First run (with dispersive term on full v̂) blew up at t=0.6. Bug-fixed by dealiasing v̂ in dispersive term + projecting state after each step.
- Result: all-finite throughout T=6. Mass(v) conserved to machine precision (0% drift). At t=1.2: clean 2-soliton train (peaks 1.87 and 1.76, separation 5.04 units). By T=6: 13 peaks all with amplitude ≥ 1.03, minimum separation 1.52 units. Phenomenon target met with high margin.

## Use of memory

**cites_bank**: `BKdV-S1` (deep synthesis) — confirmed Fourier+2/3+RK4 at dt ≤ 2e-4 is the validated baseline for BKdV at amplitudes up to 3; adopted same stack at amplitude 4 (dispersive CFL is amplitude-independent).

**rejects_bank**:
- `BKdV-S1` (CLOSED no-dealias single entry) — no-dealiasing blow-up is a general mechanism; not retried.
- `kb-kdv-noDealiasing-aliasing-artifacts` — same mechanism (aliasing creates spurious peaks); not retried.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` — IMEX-CN blows up at amplitude 3; at amplitude 4 (our IC) it would be even more likely to fail; explicitly rejected.
- `kb-gardner-cubicTerm-tightens-nonlinearCFL` — warned that IMEX dt must be rescaled with amplitude; combined with G4 warning, confirmed avoiding IMEX-CN.

**Not directly applicable**:
- `BKdV-S6` (bore-like u IC): our u0=0 starts smooth; the u bore-formation warning applies partly at late times (T≥5) when u grows large from v forcing.
- `kb-general-massConservation-insufficient-diagnostic`: followed recommendation — checked peak count and amplitudes in addition to mass.

## Final self-assessment

`pred_results/T_B.npy` satisfies the phenomenon target:

1. **≥ 2 peaks with amplitude ≥ 0.8**: **YES — 13 peaks** at T=6, all with amplitude ≥ 1.03.
   - Peak amplitudes: [1.03, 4.81, 2.72, 2.35, 4.28, 1.59, 2.63, 1.36, 2.43, 1.92, 2.49, 1.72, 1.40]
   - The soliton decomposition is clearly observable: at t=1.2 a clean 2-soliton train with amplitudes ~1.87 and ~1.76 and separation ~5 units is present.

2. **mass(v) drift < 8%**: **YES — 0.0000%** (exact machine-precision conservation, as expected for a divergence-form Fourier spectral solver on a periodic domain).

3. **Shape of output**: `pred_results/T_B.npy` has shape (11, 2, 256) — 11 snapshots at t = 0.0, 0.6, 1.2, 1.8, 2.4, 3.0, 3.6, 4.2, 4.8, 5.4, 6.0. Channel 0 = u, channel 1 = v.

The Gaussian wave packet clearly decomposes into a soliton train (2 clean solitons observable from t=0.6 onward, consistent with KdV-type inverse scattering decomposition). The subsequent increase in peak count (from 2 at T≈1-3 to 13 at T=6) reflects the growth of u through the v²/v_xx forcing and the associated back-coupling into v, as well as soliton interactions on the periodic domain.
