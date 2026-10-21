# Reasoning — T_C: Burgers bore + KdV soliton interaction

## Final method

**E1 — Fourier pseudospectral + 2/3-rule dealiasing + classical RK4**

- Spatial: Fourier pseudospectral on N=256 points, periodic domain [-15, 15] (L=30)
- Dealiasing: 2/3-rule mask (zero modes with |k_idx| > N//3 = 85) applied to every nonlinear product
- Time stepping: classical 4-stage Runge-Kutta, dt=2e-4 (40 000 steps for T=8)
- Viscosity: none
- All spatial derivatives computed spectrally: ∂_x → ik, ∂_x³ → (ik)^3
- Nonlinear products (u·u_x, v·v_x, u·v) formed from dealiased physical-space fields then FFT + dealias

The RHS implements the coupled BKdV system exactly as stated:
- `u_t = −3·u·u_x − 6·v·v_x − v_xxx`  (from `u_t + 3uu_x = −∂_x(3v²+v_xx)`)
- `v_t = −6·v·v_x − v_xxx − ∂_x(u·v)` (from `v_t + 6vv_x + v_xxx = −∂_x(uv)`)

## Iteration trace

**E1** — Fourier+2/3-dealias+RK4, no viscosity. Output: v_peak=0.6076, u_max=4.169, mass conserved, no NaN.  
**F1** — Positive. Both phenomenon targets met (v_peak≥0.5, |u_max|<5). Bore-soliton transmission clearly visible. Early stop.

## Use of memory

**kb-BKdV-S1** (cites): The CLOSED synthesis established that Fourier + 2/3 dealiasing + RK4 + dt=2e-4 is the working stack for BKdV at Nx=256. This directly guided E1's method choice. No-dealiasing route is ruled out (CLOSED).

**kb-BKdV-S6** (consulted, not blocking): The depth-3 synthesis for bore-like u IC warned that without viscosity, u_max grows to 3.41 at T=6 and TV(u) inflates 42×, while v_max dropped to 0.58 — still above the 0.5 target. Since v_max=0.58>0.5 at T=6 in BKdV-S6's experiment (different soliton position, T=6), it was reasonable to run E1 without viscosity first and observe the actual T=8 outcome. The entry is OPEN (regime-bound), not a categorical prohibition. Outcome at T=8: u_max=4.17 (higher than BKdV-S6's 3.41 at T=6, but still <5), v_peak=0.608 (above 0.5). BKdV-S6's viscosity recommendation (nu=5e-2) was considered for E2 but not needed.

**kb-burgers-fwdEuler-centralFD-Gibbs**, **kb-general-centralFD-hyperbolic-shockFormation** (rejected, CLOSED): Central FD without upwinding on the Burgers advective term is prohibited. Spectral approach used throughout.

## Final self-assessment

`pred_results/T_C.npy` satisfies the phenomenon target:

| Criterion | Value | Target | Pass |
|-----------|-------|--------|------|
| v_peak final | 0.6076 | ≥ 0.5 | ✓ |
| \|u_max\| final | 4.1691 | < 5 | ✓ |
| Bore blow-up | none | none | ✓ |
| NaN/Inf | none | none | ✓ |
| Snapshots | 9 | ≥ 5 | ✓ |

The bore-soliton interaction is clearly resolved in the 9 snapshots (t=0,1,...,8):
- t=0–1: soliton at x≈−8→−4, v_max=1.50→0.82; bore at x≈0, u_max grows 1.5→2.73
- t=2–3: soliton approaches bore (x≈−1→+1), v_max depresses to 0.60→0.61 (interaction onset)
- t=4: soliton crossing bore, v_max minimum 0.52; u_max=3.10
- t=5–7: soliton re-emerges right of bore, v_max recovers 0.69→0.84→0.85; exhibits transmission
- t=8: soliton at x=12.89, v_peak=0.608; u_max=4.17 (bore steepened, still bounded)

The soliton **transmitted** through the bore with partial amplitude reduction during passage and re-emergence at comparable amplitude afterward. It was not destroyed or fully reflected.
