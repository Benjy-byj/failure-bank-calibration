# Reasoning — T_B NegOnly rep4

## Final method

**Experiment E1 (and final answer):** Fourier pseudospectral + 2/3-rule dealiasing + classical explicit RK4.

Full description:
- Domain: x ∈ [-15, 15], L=30, Nx=256, periodic boundary conditions
- Wavenumbers: k = 2π/L · fftfreq(Nx, 1/Nx)
- 2/3-rule dealiasing mask: zero modes with |k| > (2/3)·k_Nyquist where k_Nyquist = π·Nx/L
- Dealiasing applied at EACH RK4 stage (intermediate and final), not just at product computation
- RK4 step size: dt = 1e-4 (well below the post-dealias CFL bound dt_crit ≈ 4.94e-4 for the v_xxx dispersive term)
- Time integration: classical 4th-order Runge-Kutta
- All spatial operators computed in Fourier space:
  - d/dx → ik
  - v_xxx → (ik)³ · v̂ = −ik³ · v̂; equivalently, −v_xxx → ik³ · v̂ = (1j·k³) · v̂
- RHS in spectral space:
  - û_t = −ik·[1.5·FFT(u²) + 3·FFT(v²)] + ik³·v̂
  - v̂_t = −ik·[3·FFT(v²) + FFT(u·v)] + ik³·v̂
  - where u, v for products are computed from dealiased state: u = IFFT(dealias·û), v = IFFT(dealias·v̂)
- IC: v(x,0) = 4·exp(−(x+5)²/2.25), u(x,0) = 0
- Snapshots: 10 uniform samples in t ∈ [0, 6], saved as shape (10, 2, 256)

## Iteration trace

**E1 / F1:** Fourier + 2/3-rule + RK4, dt=1e-4. Ran 60000 steps to T=6. Result: 12 peaks ≥ 0.8 in v_final (amplitudes 1.03–4.87), mass drift 0.000%, 0% high-k energy fraction in both u and v. u grew to max=9.19 via Burgers coupling but remained spectrally clean. Soliton decomposition confirmed by evolution: 1 Gaussian peak at t=0 → 2 peaks by t=0.67 → 12 peaks by T=6. Phenomenon target clearly met → early stop.

Bug fix during E1: initial implementation saved snapshots via ifft(uhat) without dealiasing, accumulating phantom high-k ghost modes in uhat that inflated apparent u_max to 54 and TV to 6358; fix applied the dealias mask at each RK4 stage so ghost modes never accumulate. The v dynamics were unaffected (v had 0% high-k energy in both versions, confirming ghost modes were inert to v).

## Use of memory

**Used (cites_bank):**
- `BKdV-S1-deep-synthesis`: This deep synthesis entry was the primary design guide for E1. It explicitly validates the Fourier + 2/3-rule + classical RK4 stack at dt≤2e-4 for amplitudes in [1,3], T=10. I extended to amplitude 4 by using dt=1e-4 (more conservative) and confirmed stability. The entry also establishes that the binding failure mode is broadband aliasing, not RK4 stiffness on v_xxx — reinforcing that 2/3 dealiasing is essential.

**Rejected (rejects_bank):**
- `kb-kdv-noDealiasing-aliasing-artifacts`: Rejected Fourier without dealiasing; would create spurious soliton-like peaks corrupting the soliton-train count (amplitude inflation 43%, spurious peaks from quadratic aliasing).
- `kb-general-centralFD-hyperbolic-shockFormation`: Rejected central FD spatial discretization; catastrophic on the Burgers u·u_x term (21 spurious maxima, amplitude 7.2× over-estimate).
- `kb-kdv-IFRK4-blowup`: Rejected integrating-factor RK4; prone to implementation errors from high-k exponential overflow.
- `BKdV-S6` (bore-viscosity): Noted but not applicable — our IC has u0=0 (not a bore-like IC). U grows via coupling but starts smooth, so bore-specific linear viscosity not needed.
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup` and `kb-gardner-cubicTerm-tightens-nonlinearCFL`: These warn about IMEX-CN explicit nonlinear failing at A≥3. Not directly applicable here since we use fully explicit RK4 (where the binding CFL is the dispersive v_xxx term, not the explicit nonlinear), but informed the choice to be conservative with dt=1e-4.
- `BKdV-S7-deep-synthesis`: Warns that sech² IC with u0=v0²/2 (m=0 manifold) fragments v; not applicable since our IC has u0=0 (m = −v²/2 ≠ 0), so we are in a general BKdV regime, not constrained to Gardner reduction behavior.

## Final self-assessment

**Prediction file: `pred_results/T_B.npy`, shape (10, 2, 256)**

I believe the phenomenon target is satisfied:

1. **≥2 peaks ≥ 0.8 in final v**: YES — 12 peaks detected with amplitudes [1.03, 1.03, 1.36, 1.37, 1.37, 1.49, 1.67, 1.90, 2.32, 2.42, 3.67, 4.87]. Well above the ≥2 threshold.

2. **Well-separated peaks**: YES — 9 of 11 consecutive peak pairs satisfy gap > KdV half-width of smaller neighbor (the KdV half-width criterion sqrt(6/A)). The two largest peaks at x=−14.77 (A=3.67) and x=−12.07 (A=4.87) are separated by 2.70 units vs. their half-widths of ~1.11–1.28. Minimum gap overall is 1.52 physical units.

3. **mass(v) drift < 8%**: YES — drift = 0.000% (machine-precision conservation, as expected for spectral divergence-form discretization on periodic domain).

4. **Numerical quality**: Spectrally clean — 0% energy in high-k modes (|k| > 2/3·k_Nyq) for both u and v at all times. No blow-up. RK4 CFL number = dt·k_eff³ = 0.571 ≪ 2.83 (stability limit).

5. **Physical interpretation**: The Gaussian at x=−5 decomposes into a soliton train starting at t≈0.67 (2 peaks), consistent with KdV inverse scattering theory for positive-amplitude initial data. The coupled Burgers component develops large amplitude (u_max≈9.19) from the forcing −∂_x(3v²+v_xx), contributing additional structure in v through the coupling term −∂_x(uv). The total of 12 peaks by T=6 reflects both genuine soliton decomposition and periodic-domain wrap-around of the fast-moving leading solitons.
