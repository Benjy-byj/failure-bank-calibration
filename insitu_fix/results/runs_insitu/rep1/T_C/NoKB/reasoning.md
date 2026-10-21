# Reasoning — T_C: Burgers bore interacting with KdV soliton

## Final method

**Experiment E2**: Fourier pseudospectral spatial discretization + explicit RK4 time integration + 2/3-rule dealiasing.

- **Domain**: x ∈ [-15, 15], Nx=256, periodic; x = linspace(-15, 15, 256, endpoint=False)
- **Wavenumbers**: k = fftfreq(256, 1/256) * 2π/30
- **Dealiasing mask**: zero Fourier modes |n| > Nx/3 = 85 (keeps 171 of 256 modes)
- **Applied at each RK4 stage**: dealiasing mask applied to FFT of u, v, and all nonlinear products (3v², uv, u·u_x, v·v_x)
- **Time step**: dt = 1e-4 (80,000 steps to T=8)
- **RHS discretization**:
  - u_t = -3·u·u_x  - ∂_x(3v² + v_xx)   [all terms dealiased]
  - v_t = -6·v·v_x  - v_xxx - ∂_x(uv)   [all terms dealiased]
  - Spectral derivatives: u_x via ifft(ik·fft(u)), v_xxx via ifft(-ik³·fft(v)), etc.

## Iteration trace

- **E1 / F1 (negative)**: Fourier pseudospectral + RK4, dt=1e-4, NO dealiasing.
  Blew up at t < 0.889 (overflow in v²). Linear stability bound |k³_max·dt| = 1.925 < 2.83 (RK4 imaginary axis limit) was satisfied, so the blow-up was attributed to **aliasing** from the quadratic nonlinear terms (3v², uv) generating energy at wavenumbers up to 2k_max that alias back and feed spurious growth.

- **E2 / F2 (positive, early stop)**: Added 2/3-rule dealiasing. Simulation completed to T=8.
  v_max(T=8) = 0.665 ≥ 0.5; max|u| = 3.64 < 5; v_mean = 0.1000 conserved exactly across all 10 snapshots; all values finite.

## Use of memory

No knowledge bank provided (NoKB condition). All decisions from general knowledge of spectral PDE numerics.

- **Not used (no bank entries)**: no kb-xxx citations.
- **General knowledge applied**: 2/3-rule dealiasing is the standard anti-aliasing technique for spectral methods with quadratic nonlinearities (Orszag 1971). The rule prevents aliasing of modes at wavenumbers > k_max/2 that would otherwise produce spurious modes above Nyquist and fold back to low modes.

## Final self-assessment

`pred_results/T_C.npy` satisfies the phenomenon target:

| Diagnostic | Value | Target |
|---|---|---|
| v_max at T=8 | **0.6648** | ≥ 0.5 ✓ |
| max\|u\| over all time | **3.64** | < 5 ✓ |
| All values finite | True | ✓ |
| v_mean conservation | 0.1000 (all 10 snapshots) | mass conserved ✓ |

**Physical interpretation**: The KdV soliton (initial amplitude 1.5 at x=-8) moves rightward and interacts with the bore (u: 1.5→0 step at x=0) between t≈1 and t≈5. The soliton's amplitude decreases during the encounter (to ~0.48 at t=4.4) but recovers to 0.665 at T=8, with the main peak now at x≈13.83 — the soliton **transmitted** through the bore (refracted), with a small dispersive tail left at x≈7.7. This is consistent with the "transmission" scenario noted in the task description.

The output array shape is (10, 2, 256) with 10 evenly-spaced snapshots from t=0 to t=8, sufficient for the parent's phenomenon evaluation.
