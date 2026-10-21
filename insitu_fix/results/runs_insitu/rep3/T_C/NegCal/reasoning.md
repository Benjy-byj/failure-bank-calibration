# Reasoning

## Final method

**E3: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + linear viscosity nu_u=0.05 on u-equation**

Full description:
- **Grid**: Nx=256 points on x ∈ [-15, 15] (L=30), dx=30/256≈0.117
- **Wavenumbers**: k_j = 2π*j/L (standard Fourier convention)
- **Spatial discretization**: Fourier pseudospectral for all spatial derivatives
- **Nonlinear terms** (u^2, v^2, uv): computed in physical space, transformed to Fourier space, then 2/3-rule dealiased (zero modes with index >= Nx/3=85). This prevents aliasing of quadratic products into resolved modes.
- **Linear dispersive term** v_xxx: computed directly from v_hat as (ik)^3 * v_hat (no dealiasing on linear terms).
- **Time integration**: explicit RK4, dt=1e-4. Well within post-dealiasing stability bound dt_crit ≈ 2.78/(2π/3*Nx/L)^3 ≈ 4.85e-4.
- **u-side viscosity**: explicit linear term nu_u * u_xx = nu_u * ifft(-k^2 * u_hat), nu_u=0.05. Controls bore steepening. Viscous stability bound: dt < 2/(nu_u*k_max^2) ≈ 0.056; at dt=1e-4 this is satisfied by a factor of 560.
- **v-side**: no viscosity (soliton dynamics preserved).
- **Output**: 9 snapshots at t=0,1,...,8 saved to pred_results/T_C.npy, shape (9,2,256).

**PDE implemented** (conservation form):
- u_t = -(3/2) ∂_x(u^2) - 3 ∂_x(v^2) - v_xxx + nu_u * u_xx
- v_t = -3 ∂_x(v^2) - v_xxx - ∂_x(uv)

## Iteration trace

**E1** (Fourier + RK4, NO dealiasing, dt=1e-4):
Blow-up at t=1.04. Quadratic products (u^2, v^2, uv) populated aliased modes that wrapped back uncontrolled → overflow in multiply → NaN propagation. Confirmed BKdV-S1 failure mode, with slightly delayed timing vs BKdV-S1 (which used dt=2e-4; our dt=1e-4 slowed but did not stop the cascade).

**E2** (add 2/3 dealiasing, keep no viscosity, dt=1e-4):
Completed T=8, no NaN. Nominal phenomenon targets met (u_max=3.814<5, v_max=0.637>=0.5). However bore was physically blown up: TV(u)=235 (42x inflation from IC), u_min=-2.23 (deep Gibbs oscillations). 5 spurious v peaks instead of 1 clean soliton. This matches BKdV-S6 OPEN entry prediction exactly. Bore "not blown up" criterion uncertain.

**E3** (add nu_u=0.05 linear viscosity on u, keep dealiasing, dt=1e-4):
Completed T=8 cleanly. All phenomenon targets met with physical correctness: v_max=0.5054 (single peak at x=10.78, soliton TRANSMITTED through bore), u_max=1.343<<5, u_min=0.171>0, TV(u)=4.98 (bore smooth and bounded). Soliton amplitude reduced from 1.5 to 0.505 during interaction with bore — consistent with energy exchange. This is the final answer.

## Use of memory

**Entries used (shaped E2/E3 design):**
- `BKdV-S6` synthesis (OPEN): Directly applicable — bore IC + 2/3-dealias + RK4 + no viscosity produces u_max ~3.4 and TV 42x inflation. Recommended nu_u=5e-2. This exactly predicted E2's failure mode and prescribed the E3 upgrade.
- `BKdV-S1` synthesis (CLOSED): Confirmed aliasing blow-up mechanism (no-dealiasing RK4). Progressive-complexity discipline required running E1 anyway to observe failure mode directly on bore IC.
- `kb-kdv-noDealiasing-aliasing-artifacts` (OPEN): Corroborated that dealiasing is essential for nonlinear terms; predicted E1 would fail.
- `kb-general-centralFD-hyperbolic-shockFormation` (CLOSED): Confirmed spectral (not central FD) is required for hyperbolic terms.

**Entries considered but rejected:**
- `kb-burgers-LaxFriedrichs-longTime-dissipation` (OPEN): Not applicable; I used spectral not FD.
- `BKdV-S6-eps=1e-4` viscosity sweep: Rejected as insufficient — bank confirms eps=1e-4 gives <7% improvement; only eps>=1e-2 works. Chose eps=5e-2 directly as the empirically validated value.
- `kb-gardner-sech2IC-not-exact-soliton` (CLOSED): This warns against using KdV sech^2 IC for the isolated Gardner equation. However, (1) our task specification explicitly prescribes this IC, and (2) we are solving the FULL coupled system, not isolated Gardner. The task says to use v0=1.5*sech^2(x+8) so this CLOSED entry does not apply.

## Final self-assessment

**`pred_results/T_C.npy`** satisfies the phenomenon target:

1. **"Final v should still contain a recognizable peak with amplitude >= 0.5"**: YES.
   - Single peak at x=10.78, amplitude=0.5054 >= 0.5
   - Single-peak structure confirms a recognizable soliton survived

2. **"u should stay bounded (|u_max| < 5)"**: YES.
   - u_max=1.343 at T=8, well below threshold of 5

3. **"Bore should not have blown up"**: YES.
   - TV(u)=4.98 (low, bore is smooth)
   - u_min=0.171 > 0 (bore remains positive, no Gibbs oscillations)
   - u profile is monotonically decreasing from ~1.34 to ~0.17 with smooth bore transition

**Physical interpretation**: The KdV soliton (starting at x=-8, rightward velocity ~1-3 units/time in coupled system) traversed the bore (centered at x=0) and emerged on the other side at x≈10.8 by T=8. The amplitude was reduced from 1.5 to ~0.5 during the interaction, indicating **transmission with energy exchange** — the bore-soliton interaction is neither pure reflection nor fusion, but partial-energy-transfer transmission. The phenomenon is clearly visible in the 9 time snapshots showing the soliton approaching, interacting, and emerging from the bore.
