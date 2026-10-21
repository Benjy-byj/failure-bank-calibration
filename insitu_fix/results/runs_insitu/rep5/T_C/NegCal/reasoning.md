# Reasoning

## Final method

**E1 (no viscosity)**: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4, dt=2e-4, Nx=256, L=30, T=8, no dissipation on either field.

Key implementation detail: the state (u, v) is pre-dealiased at the START of each RHS call (band-limited to k_eff = 2/3·k_max ≈ 17.87). This is critical — without it, the v_xxx term in the u-equation operates at the full k_max = 26.81, violating the RK4 stability bound dt_crit = 2.83/k_max^3 ≈ 1.47e-4 < dt = 2e-4. With pre-dealiasing, dt_crit = 2.83/k_eff^3 ≈ 4.96e-4 >> dt, giving 2.5× safety margin.

Nonlinear products (u·u_x, v·v_x, u·v and its derivative) are additionally dealiased.

PDE implemented as:
- u_t = −3·u·u_x − 6·v·v_x − v_xxx
- v_t = −6·v·v_x − v_xxx − ∂_x(u·v)

Snapshots: 9 snapshots at t = 0, 1, 2, 3, 4, 5, 6, 7, 8.

## Iteration trace

**E1 (iter 1)**: Fourier+2/3-dealias+RK4, dt=2e-4, no viscosity. Initial implementation missed pre-dealiasing of u, v, causing blow-up at step 17. Bug fix: pre-dealias state at each RHS call. Re-run completed T=8 successfully. Result: v_max=0.61 at T=8, min v_max=0.517 across all snapshots (always ≥ 0.5), u_max=4.17<5. Mass conserved to machine precision. PASSES phenomenon thresholds.

**F1 (from E1)**: Positive. v_max=0.61≥0.5 ✓, |u_max|=4.17<5 ✓. Bore steepened with Gibbs oscillations (u_min=−1.20, BKdV-S6 predicted failure mode) but did not blow up. Soliton transmitted through bore (peak migrated from x=−8 to x≈13 over T=8, amplitude retention 41%).

**E2 (iter 2)**: Same stack + single-component upgrade: nu_lin=5e-2 on u (per BKdV-S6 synthesis). Reduced u_max to 1.44, eliminated negative u. However, v_max dropped to 0.42 at t=4 and only recovered to 0.505 at T=8 — worse than E1. Rolled back to E1.

**F2 (from E2)**: Negative. The u-viscosity stabilized the bore but modified the bore-soliton interaction physics: with softer bore, less energy was exchanged with v, but intermediate soliton amplitude dropped below the 0.5 threshold. E1 remains superior.

## Use of memory

**Entries used**:
- `BKdV-S1` (CLOSED synthesis): Established Fourier+2/3-dealias+RK4 at dt=2e-4 as the validated baseline for BKdV amp≤3. Directly informed E1 method choice. The "pre-dealias state" note from this entry was the critical insight that fixed the E1 bug.
- `BKdV-S6` (OPEN synthesis + individual entries): Predicted that smoothed bore IC without u-viscosity gives u_max→3.41, TV inflation, v_max→0.58 at T=6. Informed the E2 escalation choice (nu=5e-2). The synthesis accurately predicted E2's outcome (u_max≤1.62 confirmed).

**Entries consulted but rejected**:
- `kb-general-centralFD-hyperbolic-shockFormation` (CLOSED): Rejected central FD for the hyperbolic component — spectral method used instead.
- `kb-kdv-IFRK4-blowup` (OPEN): Avoided IFRK4 due to implementation risk.
- `kb-kdv-explicit-RK4-stiffness-blowup` (OPEN): Warned that explicit RK4 can fragment soliton. In our system the pre-dealiasing mitigates this by reducing k_eff, and the bore-soliton problem has different stability characteristics than the isolated KdV case.

## Final self-assessment

**I believe pred_results/T_C.npy satisfies the phenomenon target.**

Key diagnostics:
- `final_v_max = 0.6076 ≥ 0.5` ✓ — recognizable dominant soliton peak at x≈13, 2.4× amplitude of next-largest peak (0.25). The soliton transmitted through the bore.
- `min_v_max_across_all_snapshots = 0.5165` (at t=4) — v stays above 0.5 throughout the simulation.
- `final_|u_max| = 4.1693 < 5` ✓ — bore bounded throughout.
- `max_|u|_all_snapshots = 4.1693 < 5` ✓ — bore never blew up.
- Mass conserved: Δ(mass_u) = 0.0%, Δ(mass_v) = 0.0% (machine precision).
- No NaN/Inf at any snapshot.

Physical interpretation: The v soliton (amplitude 1.5, starting at x=−8) moves rightward, encounters the bore around t≈2–3, reduces in amplitude during the interaction (minimum 0.52 at t=4), and partially recovers to 0.61 at T=8. This is consistent with a transmission (refraction) scenario where the soliton passes through the bore region with amplitude loss. The bore develops Gibbs-like oscillations (u_min=−1.20) due to the spectral treatment of the sharp gradient, but remains bounded.
