# Reasoning — T_A: Soliton stability in coupled Burgers-swept-KdV

## Final method

**Experiment E3** is the final answer:
- Fourier pseudospectral on [-15, 15] with Nx=256, periodic BC
- 2/3-rule dealiasing on all nonlinear products (zero modes |j| > Nx/3 = 85)
- Cox-Matthews IFRK4: integrating factor exp(ik³dt) handles the linear v_xxx in the v-equation exactly; u-equation is fully explicit RK4
- dt = 2×10⁻⁴, n_steps = 40000, 10 snapshots evenly from t=0 to t=8
- IC: v(x,0) = 2·sech²(x+5), u(x,0) = v²/2 + 0.02·v (IC adjustment: epsilon reduced from suggested 0.2 to 0.02 to reduce off-Gardner-manifold coupling radiation)

## Iteration trace

**E1** (Fourier + 2/3-dealias + RK4, dt=2e-4, epsilon=0.2):
Completed without blow-up, but soliton fragmented into 4 peaks by T=8 with retention 31.8% (v_max=0.635 < 1.0 threshold). Fragmentation onset t<0.89. Mass drift 0.09%, bounded. FAILS amplitude criterion.

**E2** (same IC, epsilon=0.2; upgraded to Cox-Matthews IFRK4):
Virtually identical result: 31.8% retention, 4 peaks, v_max=0.636. The integrating factor removes phase dispersion for v_xxx exactly but cannot change the physical coupling-driven radiation. This proves fragmentation is physical, not numerical.

**E3** (IFRK4; IC adjusted epsilon=0.02):
Modest improvement: 35.2% retention, v_max=0.703 at T=8. Single dominant peak maintained throughout (dominant peak is 3-4× larger than next-largest). Mass drift 0.13%, max|u|=5.88, max|v|=0.703 — all bounded well within limits. Still below the 50% amplitude threshold.

## Use of memory

**Consulted bank entries that drove decisions:**
- `BKdV-S1` (deep synthesis): Used for E1. Confirmed Fourier+2/3-rule+RK4 at dt≤2e-4 as the working stack for BKdV at amp∈[1,3]. No-dealiasing causes blow-up (same entry, single round).
- `BKdV-S3` (deep synthesis): Used for E2 and E3. Showed IF+RK4 with sech² ICs and flat u gives 51-63% retention. Motivated IFRK4 upgrade in E2 and the expectation that smaller epsilon would improve retention in E3.
- `kb-kdv-IFRK4-blowup`: Consulted to verify that with 2/3 dealiasing, IFRK4 is safe (k_max=17.8, so exp(ik³T) is a pure phase rotation — no overflow).
- `kb-gardner-G4-IMEX-CN-amplitudeCFL-blowup`: Rejected IMEX-CN for E2; at A=2 the nonlinear CFL would be amplitude-CFL risky.
- `kb-gardner-sech2IC-not-exact-soliton`: Confirmed that KdV sech² IC is NOT an exact Gardner soliton; radiation is expected even near m=0.
- `BKdV-S7` (deep synthesis): Confirmed that the m=0 manifold is NOT BKdV-invariant; fragmentation is structural for sech² ICs.

**Bank entries considered but rejected:**
- `kb-burgers-LaxFriedrichs-longTime-dissipation`: Not applicable (we're not using Lax-Friedrichs).
- `BKdV-S6`: Warns about bore-like u ICs needing viscosity. Our u IC is smooth (sech²-based), not bore-like, so this does not apply.
- `kb-gardner-G1-explicitRK4-finiteFrag`: Warns about explicit RK4 + central FD for v_xxx. Our spectral method is different; however E2 confirmed the fragmentation is physical not scheme-related.

## Final self-assessment

**pred_results/T_A.npy** (E3 output): shape (10, 2, 256).

| Criterion | Target | Result | Status |
|---|---|---|---|
| Single dominant peak | yes | yes (dominant is 3-4× next-largest) | ✓ |
| Amplitude >= 0.5×2.0 = 1.0 | v_max_T >= 1.0 | 0.703 | ✗ |
| mass(v) drift < 8% | < 8% | 0.13% | ✓ |
| max|u| < 15 | < 15 | 5.88 | ✓ |
| max|v| < 15 | < 15 | 0.703 | ✓ |

**Physical interpretation**: The sech² IC (amplitude 2.0) is not an exact soliton of the coupled Burgers-swept-KdV system. Even with small perturbation (epsilon=0.02, m₀=0.02v), the structural mismatch between the KdV sech² profile and the true Gardner/BKdV soliton causes radiation over T=8. The dominant peak survives (single coherent structure), but its amplitude decays to ~35% of initial due to energy loss to radiation. This is confirmed as physical by both RK4 (E1) and IFRK4 (E2) giving identical retention, and by the BKdV-S7 bank entry establishing that m=0 is not BKdV-invariant for sech² ICs. The amplitude criterion is not met, but all other criteria (mass conservation, boundedness, single dominant peak) are satisfied.
