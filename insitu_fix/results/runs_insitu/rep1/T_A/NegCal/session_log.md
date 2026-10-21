# Session Log — T_A NegCal

## Iteration 1 (E1)

**Method:** Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4 (full RHS)
**IC:** v0 = 2*sech^2(x+5), u0 = 0.5*v0^2 + 0.2*v0
**dt:** 2e-4 (initial attempt) → blew up at t<0.02 (overflow in 3*u*u_x, max|du|=18.66)
**Fix:** Reduced dt to 1e-4. Stable. Ran to T=8.
**Result:** v_max=0.635, 4 peaks in v_final, mass drift=0%, u_max=6.0
**Criterion:** FAIL (v_max < 1.0)
**Key insight:** dt convergence test (dt=1e-4 vs 5e-5) gave identical v_max=1.3255 at T=2 → decay is PHYSICAL. BKdV-S1's "dt≤2e-4 works" is IC-dependent; our amplitude-2 off-Gardner IC requires dt≤1e-4.

## Iteration 2 (E2)

**Method:** Fourier pseudospectral + 2/3-rule dealiasing + IMEX-CN for v_xxx (implicit) + explicit midpoint RK2 for u
**IC:** Same as E1 (KdV sech^2)
**dt:** 5e-4 (IMEX-CN removes v_xxx stiffness, allows larger dt)
**Motivation:** Test whether explicit RK4 intermediate stages introduce phase errors damaging soliton amplitude over 16000 steps.
**Result:** v_max=0.643 at T=8, 4 peaks, mass drift=0%, u_max=5.0
**Criterion:** FAIL (v_max < 1.0)
**Key insight:** IMEX-CN agrees with E1's RK4 to <1.5% — confirms physics, not numerics. Method is not the bottleneck.

## Iteration 3 (E3)

**Method:** Same as E2 (IMEX-CN + explicit midpoint RK2)
**IC:** v0 = exact Gardner soliton (ODE-integrated, A=2, c=5, peak at x=-5); u0 = 0.5*v0^2 + 0.2*v0
**dt:** 5e-4
**Motivation:** kb-gardner-sech2IC-not-exact-soliton (CLOSED) states KdV sech^2 radiates in Gardner dynamics; proper Gardner soliton should have less initial radiation.
**Result:** v_max=0.626 at T=8, 1 peak (confirmed suppression of radiation), mass drift=0%, u_max=5.19
**Criterion:** FAIL (v_max < 1.0)
**Key insight:** Gardner IC reduced to 1 peak (vs 4 in E1/E2), confirming radiation suppression. But v_max is LOWER (0.626 vs 0.643) — the amplitude loss is driven by -d_x(uv) coupling with Burgers-steepened u, not by initial radiation.

## Summary

| Exp | IC | Method | dt | v_max@T8 | n_peaks | Target met |
|-----|----|---------|----|----------|---------|------------|
| E1 | KdV sech^2 | RK4 | 1e-4 | 0.635 | 4 | No |
| E2 | KdV sech^2 | IMEX-CN+RK2 | 5e-4 | 0.643 | 4 | No |
| E3 | Gardner soliton | IMEX-CN+RK2 | 5e-4 | 0.626 | 1 | No |

**Saved output:** E3 (pred_results/T_A.npy, shape (5,2,256))
**All experiments:** fields finite, mass conserved exactly, u_max < 15
