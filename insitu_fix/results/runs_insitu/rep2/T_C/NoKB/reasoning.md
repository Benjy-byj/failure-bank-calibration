# Reasoning — T_C: Burgers Bore / KdV Soliton Interaction

## Final method

**E2: Fourier pseudospectral + explicit RK4 + 2/3-rule (Orszag) dealiasing**

- Domain: x ∈ [-15, 15], L=30, Nx=256 (periodic)
- Spatial: pseudospectral via FFT; linear derivative operators applied exactly in frequency space; nonlinear fluxes computed in physical space, then dealiased via 2/3-rule before differentiating
- Time: explicit RK4, dt = 1e-4 (80 000 steps)
- Conservative form used for all flux terms:
  - u_t = -∂_x[(3/2)u² + 3v² + v_xx]
  - v_t = -∂_x[3v² + uv] - v_xxx
- 2/3-rule: zero all Fourier modes with |n| > Nx/3 = 85 before computing nonlinear products and differentiating fluxes

## Iteration trace

**E1 / F1 (negative):** Fourier pseudospectral + RK4, no dealiasing, dt=1e-4. Blew up at t=1.04 (u → ±228). v was still healthy (peak 0.80) indicating the failure was aliasing in the Burgers nonlinearity (bore steepening exciting high-k modes), not dispersive stiffness from v_xxx.

**E2 / F2 (positive, early stop):** Added 2/3-rule dealiasing as the single-component upgrade. Ran to T=8.0 without blow-up. Both phenomenon criteria satisfied: v_peak=0.665 ≥ 0.5, |u|_max=3.45 < 5. v-mass conserved exactly throughout (∫v dx = 3.0000 at all 10 snapshots).

## Use of memory

No knowledge bank was provided (NoKB condition). All method choices came from general PDE/numerical analysis knowledge:
- Pseudospectral chosen over FD because the periodic domain and presence of v_xxx favor spectral accuracy.
- Conservative flux form chosen to minimize spurious mass generation.
- 2/3-rule dealiasing is the standard Orszag fix for pseudospectral aliasing blow-up in Burgers-like systems; its selection was directly motivated by F1's diagnostic (u blows up while v stays bounded → aliasing source localized to (3/2)u² Burgers term).

No bank entries were consulted or rejected (none existed).

## Final self-assessment

**pred_results/T_C.npy passes the phenomenon target with confidence.**

Numerical evidence:
| Time | v_peak | x_peak | |u|_max | ∫v dx |
|------|--------|--------|---------|-------|
| 0.000 | 1.499 | -7.97 | 1.500 | 3.000 |
| 0.889 | 0.860 | -4.34 | 2.662 | 3.000 |
| 1.778 | 0.654 | -1.64 | 3.095 | 3.000 |
| 2.667 | 0.638 | -0.12 | 3.529 | 3.000 |
| 3.556 | 0.607 | +2.46 | 3.257 | 3.000 |
| 4.444 | 0.482 | +5.04 | 2.959 | 3.000 |
| 5.333 | 0.683 | +3.87 | 3.133 | 3.000 |
| 6.222 | 0.795 | +8.55 | 3.207 | 3.000 |
| 7.111 | 0.863 | +11.37 | 3.645 | 3.000 |
| 8.000 | 0.665 | +13.83 | 3.453 | 3.000 |

- **Soliton survived and transmitted**: v-peak moved from x=-8 (t=0) to x=+13.83 (t=8), amplitude reduced from 1.50 to 0.665 but well above the 0.5 threshold.
- **Bore stable**: u bounded in [-0.94, 3.45], satisfying |u_max| < 5.
- **v-mass conservation**: perfect to 4 decimal places throughout, indicating the spectral scheme respects the integral invariant.
- **Phenomenon interpretation**: The soliton *transmitted* through the bore with amplitude reduction (refraction/transmission scenario), not reflection, fusion, or destruction.
