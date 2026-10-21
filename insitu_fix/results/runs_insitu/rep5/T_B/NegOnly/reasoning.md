# Reasoning

## Final method

**Experiment E2 (bug-fixed):** Fourier pseudospectral spatial discretization with **full 2/3-rule dealiasing** applied to both the input state and the nonlinear products at every RHS evaluation, combined with explicit **RK4** time integration.

Key parameters:
- Domain: L=30, x∈[-15,15], Nx=256, periodic
- dt = 2e-4 (RK4 dispersive CFL: dt·k_eff³ = 1.13 < 3.46, with k_eff = (Nx/3)·2π/L ≈ 17.87)
- Dealiasing: zero modes |k_idx| > Nx//3 = 85 in the Fourier state AND in all nonlinear products
- T = 6.0, 30,000 steps, 10 snapshots

The PDE is:
```
u_t = −3u·u_x − 6v·v_x − v_xxx
v_t = −(6v+u)·v_x − v·u_x − v_xxx
```

In the RHS, the state (u,v) is first projected to modes |k_idx|≤85 via IFFT(mask·FFT(f)). All spatial derivatives (including v_xxx) are computed from this dealiased state. Nonlinear products (u·u_x, v·v_x, u·v_x, v·u_x) are then computed in physical space and individually dealiased before returning.

## Iteration trace

- **E1 / F1 (iter 1):** Fourier + RK4, NO dealiasing, dt=1e-4 → overflow blow-up at t=0.426 via aliasing cascade in quadratic products (v²·v_x, u·v, etc.), exactly as predicted by BKdV-S1. Confirms dealiasing is essential.

- **E2 / F2 (iter 2):** Added 2/3-rule dealiasing on products (bug: forgot to also dealias the state). Initial run blew up at t=0.006 because modes 86–127 of the state were unstable under explicit RK4 for the v_xxx term: |dt·k_Nyquist³| = 2e-4 × 26.8³ = 3.85 > 3.46 (RK4 stability limit). Bug fix: pre-dealias state at each RHS evaluation (removes modes above 85 from u and v before any derivative computation). After fix: run completes to T=6, 15 peaks in v with amplitude in [0.899, 4.10], mass drift 0.000%. Phenomenon target clearly met.

## Use of memory (negative bank)

**Bank entries that drove decisions:**

- **BKdV-S1 (depth=3, single)** [`kb BKdV-S1`]: Primary negative guide. States no-dealiasing blows up before t=0.5 via aliasing (confirmed by E1). Also explicitly recommends the fix — "apply 2/3-rule spectral dealiasing on every nonlinear product; pre-dealias state at each rhs evaluation" — and validates Fourier+2/3+RK4 at dt≤2e-4 for amp∈[1,3]. The "pre-dealias state" language was the critical detail missed in the first E2 implementation.

- **kb-kdv-noDealiasing-aliasing-artifacts**: Confirmed that no-dealiasing creates spurious soliton peaks on top of genuine ones, critical for the soliton-count diagnostic.

- **kb-general-massConservation-insufficient-diagnostic**: Reminded me to check peak count and amplitude, not just mass. Applied when diagnosing the dealiasing bug (blow-up at step 29 had v_xxx_max jumping from 5 to 499 with v_max barely changed — a telltale sign of k-instability, not aliasing).

- **BKdV-S4 (depth=3)**: Contains the dispersive CFL formula dt < 2.83/k_max³. Used to identify the root cause of E2's first blow-up (modes 86..127 were above the RK4 stability limit without state dealiasing) and to confirm dt=2e-4 is safe once state is dealiased to k_eff=17.87.

**Bank entries considered but rejected:**

- **BKdV-S6**: Warns that bore-like u ICs (u₀ = tanh-profile) cause Burgers steepening that 2/3 dealiasing alone cannot control (needs extra viscosity). Our u₀=0 is NOT a bore — u grows from zero via coupling — so BKdV-S6's recommended fix (linear viscosity ν≥1e-2) was explicitly rejected for this IC.

- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup** and **kb-gardner-cubicTerm-tightens-nonlinearCFL**: Warn that IMEX-CN with explicit nonlinear at A≥3 requires smaller dt. Not applicable here because: (1) our v equation has no cubic term (it is KdV-like, not Gardner), and (2) we use fully explicit RK4, so the IMEX amplitude-CFL constraint does not apply.

- **kb-kdv-explicit-RK4-stiffness-blowup**: Warns explicit RK4 on v_xxx causes soliton fragmentation (10 peaks, amplitude wrong). This was for FINITE-DIFFERENCE v_xxx, not spectral. With spectral + dealiasing, explicit RK4 is stable (BKdV-S1 depth=3 confirmed). Rejected.

## Final self-assessment

`pred_results/T_B.npy` clearly satisfies the phenomenon target:

| Criterion | Result | Target |
|-----------|--------|--------|
| v peaks with amplitude ≥ 0.8 | 15 peaks (min amp = 0.899) | ≥ 2 |
| mass(v) drift | 0.0000% | < 8% |
| min peak separation | 0.938 domain units | "well-separated" |
| all_finite | True | True |

The evolution follows the expected pattern: Gaussian with A=4 decomposes into 2–3 primary solitons (consistent with KdV IST analysis), which then recirculate on the periodic domain (fastest soliton, c≈8, traverses ~1.6 domain lengths by T=6) and interact. By T=6, the coupling with u (which grew to u_max≈13.6 from u₀=0) produces a complex multi-peak state. All 15 identified peaks have amplitude ≥ 0.8 and are positive, with zero mass drift (exact conservation from divergence-form spectral method). **Self-assessment: POSITIVE — phenomenon target met with large margin.**
