# Reasoning — T_A NegCal

## Final Method (E3, saved)

**Solver:** Fourier pseudospectral on x∈[-15,15], Nx=256, 2/3-rule dealiasing (|k_idx|≤85)
**Time integration:** IMEX-CN for v_xxx dispersive term (unconditionally stable), explicit midpoint RK2 for u equation; operator-split (v first, then u using v_mid)
**dt:** 5e-4, 16000 steps to T=8
**IC:** v0 = exact Gardner soliton (A=2, c=5, peak at x=-5, computed via scipy.integrate.solve_ivp of dv/dξ=-v√(5-2v-v²/4)); u0 = 0.5*v0² + 0.2*v0

## Iteration Trace

**E1 → F1:** Explicit RK4. dt=2e-4 blew up at t<0.02 (u-Burgers steepening, max|du|=18.66). Reduced to dt=1e-4, stable. v_max=0.635 at T=8. dt convergence test confirmed PHYSICAL decay.

**D1 → E2:** Hypothesis: 80000 explicit RK4 stages accumulate phase errors damping soliton. Switch to IMEX-CN for v_xxx (energy-neutral for dispersive term, larger dt allowed). Result: v_max=0.643, agrees with RK4 to <1.5%. Method not the bottleneck.

**D2 → E3:** Hypothesis: KdV sech^2 is not a Gardner soliton — radiates immediately (bank: kb-gardner-sech2IC-not-exact-soliton, CLOSED). Proper Gardner soliton should be the attractor with less radiation. Result: v_max=0.626, 1 peak (vs 4) — radiation IS suppressed — but amplitude still decays to 31.4%. The -d_x(uv) coupling with Burgers-steepened u (max 2.4→5.2) is the irreducible loss mechanism.

## Use of Negative Knowledge Bank

- **BKdV-S1** (working stack): Validated Fourier+2/3-dealias+RK4. Used as baseline for E1. BUT: bank's dt≤2e-4 was IC-dependent (their amplitude ~1.5 Gardner IC). Our amplitude-2 off-Gardner IC required dt≤1e-4. This discrepancy is new negative knowledge.
- **BKdV-S7** (Gardner non-invariance mechanism): Confirmed — m_t|_{m=0} = (v-1)(6vv_x+v_xxx)≠0 at A=2, so manifold exit is rapid. This matches observed decay rate.
- **kb-gardner-sech2IC-not-exact-soliton** (CLOSED): Applied in E3 — proper Gardner IC reduces peak count 4→1, confirming radiation mechanism. But amplitude loss persists; coupling dominates.
- **kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup**: Rejected (our A=2 < blow-up threshold A=3). Correct rejection.

## Self-Assessment

**Phenomenon target NOT MET.** v_max at T=8 ≈ 0.626-0.643 (~32% of initial 2.0), below the 1.0 threshold (50% retention).

**Why not met:** The BKdV coupling -d_x(uv) is highly destructive when u Burgers-steepens rapidly. With u0=0.5*v0²+0.2*v0 at A=2, u_max grows from 2.4 to ~5.2 by T=2 (Burgers dynamics: u forms near-shock). The resulting large -d_x(uv) drains v's amplitude continuously. This is a genuine physical effect, not a numerical artifact (proven by dt convergence test E1 and method comparison E1/E2/E3).

**What was achieved:**
- Mass conservation: exact (0% drift across all experiments)
- Fields bounded: u_max<6, v_max<2, all finite
- Shape: single-peak soliton in E3 (radiation suppressed by Gardner IC)
- Physics confirmed: 3 independent numerical approaches agree to <3% on v_max

**What would be needed to meet target:** Either (a) smaller u0 perturbation m0 to stay closer to Gardner manifold, (b) amplitude A<1 (weaker BKdV-S7 mechanism), or (c) shorter simulation time T<4.
