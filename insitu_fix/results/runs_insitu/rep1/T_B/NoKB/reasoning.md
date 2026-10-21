# Reasoning: T_B Soliton Train Decomposition

## Final method

**Experiment E2**: Fourier pseudospectral spatial derivatives + explicit RK4 time integration + 2/3-rule dealiasing.

- **Spatial**: Fourier pseudospectral on periodic domain [-15,15] with Nx=256. All derivatives (u_x, v_x, v_xxx) computed via FFT with spectral differentiation operator ik and (ik)^3.
- **Time**: Explicit RK4 with dt=1e-4 (60000 steps for T=6.0).
- **Dealiasing**: 2/3-rule applied to all nonlinear products (u·u_x, v·v_x, u_x·v+u·v_x). Fourier modes with |k_index| > Nx/3 = 85 are zeroed before forming products.
- **CFL satisfied**: k_max^3 · dt = 26.81^3 · 1e-4 = 1.927 < 2√2 = 2.828 (dispersive stability).
- **IC**: v(x,0) = 4·exp(-(x+5)²/2.25), u(x,0) = 0 (reference IC unchanged).

## Iteration trace

- **E1 / F1** (negative): Fourier pseudospectral + RK4 without dealiasing. Blew up at t=0.6 (step 6000) with arithmetic overflow in nonlinear multiply terms. Cause: aliasing instability from quadratic nonlinear products (6v·v_x, 3u·u_x, ∂_x(uv)) generating energy at aliased high wavenumbers. The strong Gaussian (amplitude 4) drives intense nonlinear activity from t=0.

- **E2 / F2** (positive): Added 2/3-rule dealiasing as the single-component fix for the aliasing failure mode. Ran to T=6.0 without NaN. Final v shows 12 well-separated soliton peaks with amplitude ≥ 0.8, minimum separation 1.52 x-units. Mass of v conserved to 0.00% drift across all 10 snapshots.

## Use of memory

No knowledge bank was available (NoKB condition). All method choices were based on general PDE numerical analysis:
- **Pseudospectral** chosen because v_xxx requires high-order spatial accuracy; central FD would need impractically high-order stencils at Nx=256 on this domain.
- **Explicit RK4** chosen as the simplest stable time integrator for the dispersive + advective PDE class.
- **2/3 dealiasing** is the classical Orszag dealiasing rule for pseudospectral methods with quadratic nonlinearity — standard escalation from E1's aliasing blowup.

## Final self-assessment

**Phenomenon target met** (early stop after 2 iterations).

Diagnostics from `pred_results/T_B.npy` (shape 10 × 2 × 256):
- **Soliton train**: 12 peaks in final v with amplitude ≥ 0.8 and minimum x-separation 1.52 units. Largest peaks: 5.158, 3.449, 2.795, 2.356, 2.187, 1.847 (>> target of ≥2 peaks at ≥0.8).
- **Mass drift**: 0.00% across all 10 snapshots (target: <8%).
- **Stability**: No NaN, no energy blow-up, smooth evolution throughout [0, 6.0].

The Gaussian wave packet (amplitude 4, width σ=1.5, centered at x=-5) undergoes dispersive decomposition into a train of solitons consistent with KdV-type integrable inverse scattering, confirming the phenomenon target for T_B.
