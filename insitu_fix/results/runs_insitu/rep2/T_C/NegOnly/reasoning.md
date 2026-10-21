# Reasoning: T_C Burgers bore + KdV soliton interaction

## Final method

**Experiment E3** is the final answer.

- **Spatial**: Fourier pseudospectral on x ∈ [-15, 15], Nx=256, periodic
- **Dealiasing**: 2/3-rule (keep |k_index| ≤ 85 = Nx//3)
- **Time integrator**: Classical explicit RK4
- **dt**: 2e-4 (satisfies k³ CFL after dealiasing: dt·k_max³ ≈ 1.14 < 2.83)
- **Viscosity**: nu_u = 1e-2 explicit linear viscosity on u_xx (added to u-equation RHS only; stable: nu·k_max²·dt ≈ 6e-4 << 2.79)
- **Output**: 9 snapshots at t = 0,1,2,...,8

The u-equation RHS is:  `-3·u·u_x - 6·v·v_x - v_xxx + 0.01·u_xx`
The v-equation RHS is:  `-6·v·v_x - v_xxx - ∂_x(u·v)` (no viscosity on v)

## Iteration trace

**E1** (Fourier + 2/3-dealias + RK4, no viscosity, dt=2e-4):
- v_max(T=8) = 0.607, u_max = 4.17 (borderline, approaching limit of 5)
- TV(u) = 160 (42× inflation from IC): Gibbs oscillations on bore (no NaN, consistent with BKdV-S6)
- Partial pass: v criterion met but u is risky; bore accuracy blown up

**E2** (same + nu_u = 5e-2 on u_xx, single addition):
- v_max(T=8) = 0.505, u_max = 1.44, TV(u) = 7.18
- Bore excellently controlled; but nu_u=5e-2 over-diffuses u background, indirectly damping v through coupling -∂_x(uv)
- Borderline pass: v_max barely above 0.5

**E3** (same as E2 but nu_u = 1e-2, single parameter reduction within same component):
- v_max(T=8) = 0.5946, u_max = 1.708, TV(u) = 21.02
- Bore controlled (TV within BKdV-S6 prediction of ≤27 for nu=1e-2)
- Clear pass on all phenomenon targets

## Use of memory

**kb-BKdV-S6** (deep synthesis, negative): Directly drove E2 and E3 choices.
- E1→E2: "Without u-side viscosity, Fourier+2/3+RK4 on bore ICs produces TV 42× inflation; nu_lin=5e-2 is the recommended default."
- E2→E3: "nu>=1e-2 yields u_max_final<=1.62, TV(u)_final<=27" — minimum sufficient viscosity.
- Used: recommended single-component addition (linear u-viscosity) and minimum sufficient value.

**BKdV-S1** (deep synthesis, negative): Confirmed Fourier+2/3-rule+RK4 at dt≤2e-4 as the working baseline stack (E1 choice).

**Rejected entries**:
- `kb-burgers-fwdEuler-centralFD-Gibbs`, `kb-general-centralFD-hyperbolic-shockFormation`: Central FD on hyperbolic terms would produce Gibbs catastrophe; chose spectral instead.
- `kb-kdv-noDealiasing-aliasing-artifacts`, `kb-gardner-G3-noDealiasing-cubicAliasing`: No dealiasing leads to spurious peaks; applied 2/3-rule throughout.
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: Lax-Friedrichs would over-diffuse bore over T=8; rejected as global diffusion scheme.
- `kb-kdv-IFRK4-blowup`: IFRK4 without careful implementation blows up; used safer explicit RK4 instead.

## Final self-assessment

`pred_results/T_C.npy` (shape: (9, 2, 256)) satisfies the phenomenon target:

| Criterion | Value | Pass? |
|-----------|-------|-------|
| v_max(T=8) ≥ 0.5 | 0.5946 | ✓ |
| \|u_max\|(T=8) < 5 | 1.708 | ✓ |
| Bore not blown up | TV=21, no NaN | ✓ |

Physical narrative: The soliton (v₀ = 1.5·sech²(x+8), starting at x=-8) propagates rightward and encounters the bore (u₀ = 1.5·(1-tanh(x/0.5))/2, centered at x=0) around t≈2-3. The soliton is significantly attenuated during the bore interaction (v_max drops to ~0.46 at t=6), then re-emerges at x≈10.9 with amplitude 0.595 at T=8 — consistent with soliton transmission/refraction through the bore with amplitude reduction.

**Confident: phenomenon check should pass.**
