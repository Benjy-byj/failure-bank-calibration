# In-situ scope-calibration coding sheet (BLIND — code before reading Claude's pass)
Source: github.com/hch-wang/Negative_Knowledge, reproduction/section4/logs/nk_records/*_r*.json (21 per-round records).
## Rubric (code each record)
- TESTED SCOPE: what configurations/regimes the round actually ran (list params, ICs, ranges).
- ASSERTED SCOPE: what the record's `failure.scope` + rationale claim rules out (local / regime / general; what regime).
- CALIBRATION CODE: M = matched (asserted ⊆ tested); E+ = extrapolated beyond tested WITH an explicit mechanistic argument; E− = extrapolated WITHOUT argument; P = not a failure at all (positive finding forced into failure typing).
- Note any numeric evidence in the record (n runs, seeds, effect sizes, uncertainty) — expected: none.

## BKdV-S1_r1
- schema: scope=general_failure | action=change_method | layer=method_failure | degree=unstable | risk=medium_risk_drift | is_trivial=False
- ROUTE: Fourier pseudospectral derivatives (Nx=256, L=30) + classical RK4 over full explicit RHS (v_xxx treated explicitly), NO 2/3-rule dealiasing, NO IMEX. IC v0=1.5*sech^2(x+5), u0=v0^2/2, dt=2e-4, T=10.
- OBSERVATION: Blow-up before t=0.5: RuntimeWarning 'overflow in multiply' on v*v then u*v, then 'invalid value in fft'; first scheduled diagnostic at t=0.5 already reports sup=NaN, mass_v=NaN, finite=False, reached_T10=False.
- RATIONALE: Quadratic products (v^2, u*v, v*v_x) on a Fourier grid populate wavenumbers above Nx/3; without 2/3 truncation those aliased modes wrap back into resolved modes with no dissipation. Co-candidate: dt=2e-4 sits marginally above the pure-RK4 v_xxx CFL ~1.47e-4 for k_max=pi/dx.
- RECOMMENDED: Keep RK4 and dt=2e-4, but apply 2/3-rule spectral dealiasing on every nonlinear product (zero modes with |k_idx|>Nx/3=85; pre-dealias state at each rhs evaluation). This isolates aliasing vs v_xxx stiffness in one experiment.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S1_r2
- schema: scope=regime_bound_failure | action=change_method | layer=method_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: Fourier pseudospectral + 2/3-rule dealiasing (zero |k_idx|>Nx/3=85, 171/256 modes) on every nonlinear product (v^2, u*v, v*v_x, u*u_x) + classical explicit RK4 over full RHS incl. v_xxx; Nx=256, L=30, dt=2e-4, IC v0=1.5 sech^2(x+5), u0=v0^2/2, T=10.
- OBSERVATION: Reached T=10 cleanly: mass_v conserved <1e-12 (3.000000e+00), sup bounded 3.5-4.0 (final 3.97), tail_frac above 2/3 band ~2e-18 (machine zero), energy grew 2.08->3.69 (physical, not artifact), elapsed 22.66s, no NaN/warnings.
- RATIONALE: Positive finding: 2/3-rule cutoff blocks alias-folded modes from quadratic products feeding resolved band, isolating aliasing (not v_xxx stiffness) as R1's dominant failure. Cutoff also lowers effective k_max from pi/dx to (2/3)pi/dx, raising RK4 dispersion CFL bound from ~1.47e-4 to ~4.94e-4, so dt=2e-4 is now safely below.
- RECOMMENDED: Extend by raising amp from 1.5 to 3.0 (top of requested [1,3] range) with identical stack (Nx=256, dt=2e-4, 2/3-dealias, RK4) to probe second failure mode (shock-front aliasing in u from u*u_x or v gradient-steepening exceeding 2/3 band); diagnose via separate sup_u/sup_v and edge_frac in top 10% of resolved band.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S1_r3
- schema: scope=regime_bound_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (dt=2e-4, Nx=256, L=30); IC v0=amp*sech^2(x+5) with amp=3.0 (top of [1,3]), u0=v0^2/2; T=10; track sup_u, sup_v, mass_v, edge_frac.
- OBSERVATION: Reached T=10 cleanly: mass_v=6.0 conserved to <1e-12, sup_u rose 4.49->~10.5 with oscillations, sup_v decayed 3.0->1.16, edge_frac peaked ~3e-6 (well below 1e-4 alert), no NaN/overflow, elapsed 22.4s.
- RATIONALE: Positive finding: the predicted second failure mode (high-amp gradient steepening of u or Burgers-side under-resolution at the 2/3 band) did not materialize at amp=3, T=10. The 2/3 cutoff raises dispersion-CFL above dt=2e-4 and u-steepening stayed band-resolved.
- RECOMMENDED: To experimentally hit a second failure mode, stress an orthogonal axis: either raise dt above the post-dealias CFL bound ~4.94e-4 (e.g. dt=8e-4 with same RK4) to trigger v_xxx dispersion stiffness, or extend T to 50-100 / use Burgers-dominant IC to force shock formation requiring MUSCL-Godunov on u*u_x.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S2_r1
- schema: scope=local_failure | action=narrow_claim | layer=measurement_failure | degree=partial | risk=medium_risk_drift | is_trivial=True
- ROUTE: Baseline diagnostic sweep of 5 candidate conserved functionals (C1=int u, C2=int v, C3=int uv, C4=(1/2)int(u^2+v^2+v_x^2), C5=int m^2 with m=u-v^2/2) on soliton IC v0=1.5 sech^2(x+5), u0=0, T=20, Fourier pseudospectral Nx=256, IMEX-CN + midpoint RK2, dt=2.5e-4.
- OBSERVATION: C1 stayed at O(1e-15) and C2 stayed at 3.0 to O(1e-15) (machine precision); C3 drifted 0 -> +0.539 with excursions ~1.81; C4 grew 2.70 -> 5.90 (+119%); C5 grew 1.16 -> 9.54 (+724%); sup-norm ~3.5, no blowup, finite throughout.
- RATIONALE: Both u- and v-equations are in divergence form on a periodic domain, so int u dx and int v dx are conserved by construction — numerics merely echo the analytical fact. Worse, u0=0 makes C1 conservation indistinguishable from a u=>0 invariance for this specific IC, so the C1 measurement cannot discriminate structural vs IC-symmetry conservation.
- RECOMMENDED: Re-run with u0 having nonzero spatial mean (e.g. u0 = 0.4 sin(2*pi*x/L) + 0.2 cos(6*pi*x/L) + 0.15, v0 = 0.6 cos(2*pi*x/L) + 0.3 sin(4*pi*x/L) + 0.10) to break u=>0 invariance and confirm C1/C2 are IC-invariant structural conservation laws; same solver and diagnostics, T=10.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S2_r2
- schema: scope=general_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: IC-invariance probe: same Fourier+2/3-dealias+IMEX-CN/midpoint-RK2 solver (Nx=256, dt=2.5e-4, T=10); IC changed to smooth multi-mode periodic u0=0.4sin(2pi x/L)+0.2cos(6pi x/L)+0.15, v0=0.6cos(2pi x/L)+0.3sin(4pi x/L)+0.10; track C1..C5.
- OBSERVATION: C1=4.5 and C2=3.0 held to 1.6e-14 / 3.6e-15 (IC-invariantly conserved, not just stuck at 0). C3, C4, C5 drift monotonically and faster than E1: rel_drift C3=+33, C4=+15.7, C5=+34.5 over T=10; sup-norm grows 0.9->6.5, no blowup.
- RATIONALE: C1, C2 are divergence-form integrals so conserved by construction regardless of IC (machine-precision drift). C4 = (1/2)int(u^2+v^2+v_x^2)dx is not the BKdV Hamiltonian: by-hand IBP gives d/dt C4 = +(5/2)int u_x v^2 + int u_x v_xx (cubic residual), monotonic growth signals wrong-functional, not numerical drift.
- RECOMMENDED: Run a numerical-artifact control (E3): keep E1 soliton IC and vary dt by ~5x (e.g. 5e-4 vs 1e-4 at Nx=256) and Nx by 2x (256 vs 512 at dt=2.5e-4) over T=5; if C3/C4/C5 drift ratios ~ 1 across dt, drift is physical; otherwise it scales as dt^p. Separately, search for true energy with cubic terms (int u v^2 dx, int v^3 dx, int v_x u dx).
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S2_r3
- schema: scope=general_failure | action=abandon_route | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: dt/Nx-scaling control for C1..C5 drifts: 3 configs at E1 IC (v0=1.5 sech^2(x+5), u0=0), T=5: A(dt=5e-4,Nx=256), B(dt=1e-4,Nx=256), C(dt=2.5e-4,Nx=512); Fourier pseudospectral + 2/3 dealias + IMEX-CN/RK2.
- OBSERVATION: A vs B (5x dt change at Nx=256): drift ratios C3=1.002, C4=0.992, C5=0.996 (inferred order ~0). C1,C2 drifts ~1e-15 across all configs. Nx 256->512 shifts drifts by 2-15% only.
- RATIONALE: dt-invariance of C3/C4/C5 drift (ratio~1 over 5x dt change) shows the drift is physical, not numerical: it persists in the dt->0 limit. C1,C2 sit at FFT round-off because they are exact divergence-form mass invariants. No 'slow-drift' candidate exists in the proposed C1..C5 set.
- RECOMMENDED: Search for a true BKdV Hamiltonian beyond the C1..C5 candidate list: build trial functionals with cubic densities (e.g. int(u*v^2)dx, int(v^3)dx, int(v_x*u)dx) and combinations involving v_xx; re-run E3-style dt/Nx scaling to identify any quantity whose drift -> 0 as dt -> 0.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S3_r1
- schema: scope=regime_bound_failure | action=narrow_claim | layer=measurement_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: Scan 5 v-IC families (G_gauss, S_sech2, N_noise, P2_twopulse, K_sin) at A=0.8 on Nx=256, L=30 box, flat u, T=12, dt=2.5e-4; coherence = (npeaks_v<=3) AND (vmax>=0.5) AND (frac_low_v>=0.5).
- OBSERVATION: P2_twopulse COHERENT (vmax=0.67, npk=2, fracL=1.00). G/S structurally one-peak but vmax dropped to 0.42-0.46 (fails 0.5 threshold). N_noise (vmax0=3.77) and K_sin (L2=3.10) blew up to NaN at t=1.49 and t=8.38.
- RATIONALE: Two confounders: (i) the IC normalization fixed vmax0=A=0.8 but not L2, so noise/sinusoid carried much larger energy (L2=3.1-4.4) — their 'incoherence' is amplitude-driven, not family-driven. (ii) the vmax>=0.5 cutoff mislabels naturally-radiating single Gaussians as INCOHERENT despite single-peak, low-k spectrum.
- RECOMMENDED: In E2, equalize v-L2 norm across IC families (e.g. fix L2_v0=1.3) and either lower the coherence vmax threshold to ~0.4 or replace it with a peak-prominence/lock-corr criterion; for broadband ICs (N, K) reduce A so they survive T=12 without dealiasing-band overflow.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S3_r2
- schema: scope=regime_bound_failure | action=change_method | layer=hypothesis_failure | degree=contradicted | risk=medium_risk_drift | is_trivial=False
- ROUTE: Amplitude scan on sech^2(x+2,width=1.5) v-seed with flat u, A in {0.1,0.2,0.3,0.4,0.5,0.6,0.8,1.0,1.2}; same Fourier pseudospectral + RK4 + integrating-factor stack as E1; T=12, dt=2.5e-4 (1e-4 for A>=1). Measured vmax_late, npeaks_v, fracL_v (k<=2), lock_corr, and new retention=vmax_late/A.
- OBSERVATION: Across all 9 amplitudes: npeaks=1 (or 2 at A<=0.2), fracL_v>=0.993, retention 0.51-0.63, no blowup. Strict vmax>=0.5 only met at A>=1.0 (artifact of absolute threshold). lock_corr non-monotonic, peaks 0.79 at A=0.4, drops to -0.19 (A=0.1) and 0.19 (A=1.2).
- RATIONALE: BKdV's localized basin is amplitude-scale-free for sech^2 seeds: the cubic v^2 nonlinearity rescales with A but stays self-focusing, so any A produces a single coherent pulse with ~50-60% retention. There is no A_c inside the localized family; the phase boundary lives on the IC-spectral-shape axis, not amplitude.
- RECOMMENDED: Move off the amplitude axis: fix A=0.6 sech^2 and sweep additive Gaussian-envelope white noise sigma in {0,0.05,0.1,0.2,0.3,0.4,0.6,0.8} to interpolate between localized and broadband ICs; track fracL_v and lock_corr (drop count_peaks as primary — it is noise-texture-sensitive) to locate the soft sigma_c.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S3_r3
- schema: scope=regime_bound_failure | action=narrow_claim | layer=measurement_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: E3: noise-σ sweep on sech^2 seed (A=0.6, width 1.5, x0=-2) with Gaussian-envelope white noise normalized to vmax=σ; σ∈{0,0.05,...,0.80}; Fourier pseudospectral solver (Nx=256, L=30, dt=2.5e-4, T=12); diagnostics vmax_late, npeaks_v, fracL_v (|k|≤2), fracH_v (|k|≥4), lock_corr.
- OBSERVATION: No blow-up at any σ. fracL_v slides smoothly 0.999→0.545 as σ:0→0.80; lock_corr stays ~0.58 up to σ=0.20 then collapses to 0.11 by σ=0.60. npeaks_v jumps 1→10 already at σ=0.05 (metric artifact: counts tail ripples). Soft transition σ_c≈0.30–0.40 by lock; no sharp phase boundary.
- RATIONALE: The E1 coherence heuristic uses npeaks_v with a relative height_frac=0.5 threshold; under additive noise even tiny tail ripples above min_floor=0.02 register as peaks, decoupling npk from physical incoherence. The true IC→coherence map is continuous in σ — spectral-band energy and lock_corr resolve it, peak-count does not.
- RECOMMENDED: Replace npeaks_v with a smoothed/prominence-based peak counter (e.g. scipy.signal.find_peaks(v, prominence=0.1*vmax, distance=Nx//20) on a Gaussian-filtered field) and adopt a multi-metric coherence label (lock_corr≥0.3 AND fracL_v≥0.7); then refine σ_c∈[0.20,0.50] at finer resolution and test x0/width robustness.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S4_r1
- schema: scope=local_failure | action=change_method | layer=method_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: BKdV baseline reference run on Gardner-manifold IC v0=1.5 sech^2(x+5), u0=v0^2/2 (m0=0); pre-validated Fourier pseudospectral + 2/3-dealias + IF on v_xxx + RK4 stack at dt=5e-4, Nx=256, nu_h=1e-22, T=10. Diagnostics: ||m||_L2, ||m||_inf, L2_u, L2_v, mass_u/v, energy=int 0.5(u^2+v^2+v_x^2)dx, lock_corr, low/high spectral partition.
- OBSERVATION: Run completed in 3.3s, no blow-up. mass_u/v conserved to 1e-9. m_l2: 0->2.456, m_inf: 0->3.667, lock: 1.0->0.1997, L2_u: 1.076->2.489, L2_v: 1.732->0.829, energy drift +8.2% (3.279->3.547), u_peak 1.125->3.67 (front sharpening), v_peak 1.5->0.55, eh_u(T)=0.161 (high-k content in u).
- RATIONALE: Positive setup round: the baseline ran cleanly and produced finite, mass-conserving end-state values. But energy already drifts +8.2% and u develops high-k content (eh_u=0.161) at Nx=256, hinting the spatial cutoff is being pushed; the numbers are reference values, not yet a claim about convergence. Real informativeness requires the resolution sweep planned for E2/E3.
- RECOMMENDED: Run E2: double Nx 256->512 keeping dt=5e-4 and nu_h=1e-22 fixed as a one-parameter sensitivity probe. Compare t_end values (m_l2, m_inf, L2_u, L2_v, lock, energy, u_peak, eh_u) against this baseline at the prompt's 5% shift threshold. Anticipate co-constraints among (nu_h, dt, Nx) via explicit-RK4 hyperviscous stability bound dt <= 2/(nu_h*k_max^16) and u-equation v_xx dispersion CFL ~2.83/k_max^3.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S4_r2
- schema: scope=regime_bound_failure | action=change_method | layer=hypothesis_failure | degree=contradicted | risk=high_risk_false_progress | is_trivial=False
- ROUTE: E2: Nx 256->512 single-parameter probe on sech^2 BKdV IC (v0=1.5 sech^2(x+5), u0=v0^2/2) at T=10, dt=5e-4, nu_h=1e-22 with k^16 hyperviscosity + 2/3 dealias + explicit RK4 on v-IF; measure end-state m_l2, energy, lock_corr
- OBSERVATION: E2a (naive) NaN at step 4; E2b (nu_h/2^16 rescale) NaN at step 193; only E2c (nu_h rescaled AND dt=1e-4) stable. At Nx=512: energy -51%, m_l2 -33%, lock_corr 0.20->0.48 (+139%), all > 5% threshold
- RATIONALE: Two distinct CFL constraints co-couple Nx with (dt, nu_h): hyperviscous bound dt < 2/(nu_h k_max^16) and dispersion CFL dt < 2.83/k_max^3 from -ik*v_xx in u-equation (not absorbed by v-IF). Naive Nx doubling violates both, so 'single-parameter' is ill-posed; once stabilized, Nx=256 is shown sub-converged.
- RECOMMENDED: Round 3: hold Nx=256, vary only nu_h (e.g., 1e-22 -> 1e-24 and 1e-20) at dt=5e-4 to test if hyperviscosity is independently sensitive; ALSO add a converged-reference run at Nx=1024 with dt=5e-5, nu_h rescaled by 2^32, to certify Nx=512 itself isn't still drifting.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S4_r3
- schema: scope=regime_bound_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=high_risk_false_progress | is_trivial=False
- ROUTE: Vary hyperviscosity ν_h at fixed Nx=256, dt=5e-4 on IC v0=1.5*sech^2(x+5), u0=v0^2/2, T=10; four sub-runs E3a(ν_h=1e-18,dt=5e-4), E3b(1e-26,5e-4), E3c(1e-18,dt=1e-5 rescued), E3d(1e-22,dt=1e-4 trivial check). Diagnostics: m_l2, lock_corr, energy, u_peak, eh_u/v.
- OBSERVATION: E3a NaN at step 6 (HV stab bound dt≲2.8e-5 violated). E3b stable, max|Δ%|=11.7% vs E1 (7/10 diags <5%). E3c stable, max|Δ%|=277% (lock 0.20→0.75, energy −71%, u_peak −76%, eh_u −97%). E3d stable, max|Δ%|=13.2% on eh_u, rest <7%.
- RATIONALE: ν_h is asymmetrically sensitive at Nx=256: weakening is a no-op because 2/3-dealias truncation already supplies the regularization, but strengthening 1e4× actively damps high-k content and selects a different attractor branch (smooth low-amplitude locked state). The 'ν_h is harmless numerical regularization' assumption is falsified in the strong direction.
- RECOMMENDED: At Nx>=512 with co-rescaled (dt, ν_h) per E2c, re-run an HV ladder ν_h ∈ {1e-30, 1e-26, 1e-22} (under-resolved regime is now removed); compare lock_corr and energy_T to E2c to test whether the strong-HV branch (E3c) persists when truncation is no longer the dominant regularizer, vs whether it was an under-resolution artifact.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S5_r1
- schema: scope=general_failure | action=narrow_claim | layer=hypothesis_failure | degree=contradicted | risk=medium_risk_drift | is_trivial=False
- ROUTE: E1 baseline: v0=1.0*sech^2(x+5), u0=v0^2/2 (m_0=0); BKdV on [-15,15] Nx=256, T=15, dt=1e-4; Fourier pseudospectral + 2/3 dealias + IMEX-CN on v_xxx + MUSCL-Godunov on 3 u u_x; measure mass, energy, m_norm, v_peak.
- OBSERVATION: m_norm grows 0 -> 2.92 by T=15; v_peak collapses from 1.00 to ~0.4 within t<1 then oscillates chaotically (range [0.40, 1.00]); energy(u,v) drifts +679%; mass_v conserved to 0 ppm; no coherent traveling peak.
- RATIONALE: Algebra m_t|_{m=0} = (v-1)(6 v v_x + v_xxx) is generically nonzero for sech^2 ICs, so the m=0 set is NOT an invariant manifold of full BKdV. The off-manifold drift radiates the peak immediately, giving chaotic dispersive flow rather than a coherent Gardner-like soliton.
- RECOMMENDED: Reframe baseline as a chaotic-dispersive reference and measure perturbation growth as ||v_perturbed - v_base||_L2 along the chaotic trajectory (E2-style); start with a structured single-mode delta_v=0.05*sin(2*pi*5*x/L) to separate Lyapunov drift from k-selective response.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S5_r2
- schema: scope=regime_bound_failure | action=change_method | layer=hypothesis_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: E2: E1 baseline IC (v0=sech^2(x+5), u0=v0^2/2, amp=1.0) + structured single-mode delta_v0 = 0.05*sin(k0*x), k0=2pi*5/L (Fourier mode 5); diagnostic = ||v_E2(t)-v_E1(t)||_L2 over t in [0,15] with dt=1e-4, Nx=256, L=30.
- OBSERVATION: ||delta_v||_L2 stays flat at ~0.19-0.22 (1x initial) for t in [0,13]; jumps to 0.358 at t=14 and 1.153 at t=15 (~6x). Full-window fit gives growth rate +0.0493/unit dominated by the late-time jump; early-time rate ~0.
- RATIONALE: Mode 5 (k0~1.05) is a low-k perturbation with small delta_v_x/v_xx/v_xxx, so the coupling u_t -= d_x(3 v^2 + v_xx) injects little forcing; there is no linear dispersion-relation pole at this k, so no direct linear amplification. Late-time jump reflects indirect nonlinear cascade or onset of baseline chaotic separation, not mode-5 instability.
- RECOMMENDED: E3: replace structured mode-5 sin perturbation with zero-mean Gaussian white-noise delta_v0 rescaled to the SAME L2 norm (0.1936) (np.random.default_rng(42).standard_normal scaled); track ||v_E3-v_E1||_L2 vs E2 to test k-selectivity (high-k carries large derivatives that drive coupling).
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S5_r3
- schema: scope=regime_bound_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: E3: sech^2(x+5) baseline (amp=1.0) + zero-mean broadband Gaussian noise on v (rng seed=42), rescaled to ||delta_v0||_L2=0.1936 (matched to E2's mode-5 sin); same IMEX-CN/MUSCL stack, T=15, dt=1e-4, Nx=256, L=30. Observable: ||v_E3(t)-v_E1(t)||_L2 vs E2 trajectory.
- OBSERVATION: ||dv||_L2 grows ~exp(1.02 t): 0.194@t=0 -> 0.256@t=1 -> 5.66@t=4 -> 30.8@t=5; ratio E3/E2 climbs from 1.24 to 143.5 over t=1..5; numerical blow-up (v_peak=14.7, sup=15.6, then nan) at t~5.5, while matched-norm mode-5 stayed flat.
- RATIONALE: Positive finding for k-selectivity: high-k components of delta_v have small L2 but large v_xxx, and the explicit coupling u_t -= d_x(3 v^2 + v_xxx) injects huge forcing into u, driving runaway. But the late-time state is numerical blow-up, not a saturated physical regime, so 'into what state' is not answered.
- RECOMMENDED: Re-run E3 at higher resolution (Nx=512 and 1024) with same seed and tighter dt (e.g. 2.5e-5) to test stack-dependence of the +1.02/unit growth rate; then sweep single-mode delta_v across k-index k=1..N/3 with eps fixed to map a growth-rate dispersion lambda(k) and confirm continuum k-selectivity.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S6_r1
- schema: scope=regime_bound_failure | action=change_method | layer=method_failure | degree=unstable | risk=high_risk_false_progress | is_trivial=False
- ROUTE: Pre-validated stack (Fourier pseudospectral + 2/3-rule dealias + classical RK4, dt=1e-4, Nx=256, L=30) with NO u-side viscosity/hyperviscosity/filter on IC u=1.5(1-tanh(x/0.5))/2 (smoothed bore) + v=1.5 sech^2(x+5), T=6.
- OBSERVATION: No IEEE blow-up; mass_u exactly preserved (22.589). But u_max grows IC 1.5 -> 3.41 (~2.3x), u_min dives to -1.07, TV(u) inflates 3.0 -> 125.8 (42x), mid-band spectral ratio 0.3% -> 25%; v_max collapses 1.50 -> 0.58.
- RATIONALE: 2/3-rule dealiasing only zeroes |k|>2/3 k_max to prevent aliasing OF products into resolved modes; it does NOT dissipate energy already inside the resolved band. Burgers self-flux 3 u u_x steepens the bore and piles Gibbs energy just below the cutoff, then leaks into v via -d_x(uv).
- RECOMMENDED: Add explicit linear viscosity term eps*u_xx in the u-RHS (computed spectrally as ifft(-k^2*fft(u))) with eps=1e-4 as the conventional starting value, treated explicitly inside RK4; sweep upward if insufficient.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S6_r2
- schema: scope=regime_bound_failure | action=change_method | layer=hypothesis_failure | degree=contradicted | risk=medium_risk_drift | is_trivial=False
- ROUTE: Pre-validated Fourier+2/3-dealias+RK4 stack on BKdV with explicit linear viscosity eps*u_xx, eps=1e-4, on u-equation; IC: u0=1.5*(1-tanh(x/0.5))/2 bore + v0=1.5*sech^2(x+5); Nx=256, L=30, dt=1e-4, T=6.
- OBSERVATION: eps=1e-4 essentially indistinguishable from eps=0 (E1): u_max 3.41->3.18 (~7%), TV(u) 126->124 (~1.4%), u_min still -0.77; mid-k energy ratio still grows to 0.129; Gibbs/shock blow-up not suppressed.
- RATIONALE: Damping rate eps*k^2 ~ 0.032 at 2/3 k_max gives e^{-0.19}~0.82 over T=6, while the 3*u*u_x nonlinear cascade injects high-k energy faster; scaling needs eps*k_max^2 >> u_max*k_max, i.e. eps >> u_max/k_max ~ 0.17.
- RECOMMENDED: Sweep dissipation strengths: linear viscosity eps in {1e-3, 1e-2, 5e-2} via explicit eps*u_xx, AND hyperviscosity nu_h*(-1)^{p+1}*d^{2p}/dx^{2p} with p=4 (k^8 weighting) for nu_h in {1e-8,...,1e-6}, measuring TV(u), u_max, mid-k energy ratio to find minimum sufficient floor.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S6_r3
- schema: scope=regime_bound_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=medium_risk_drift | is_trivial=False
- ROUTE: Sweep u-side dissipation atop Fourier+2/3-dealias+RK4 (Nx=256, dt=1e-4, T=6) for smoothed bore u0=1.5(1-tanh(x/0.5))/2 + v0=1.5 sech^2(x+5): linear nu*u_xx in {1e-3..1e-1} and k^8 hyperviscosity nu_h in {1e-14..1e-9}.
- OBSERVATION: Linear nu>=1e-2 yields u_max_final<=1.62, TV(u)_final<=27, u_min_final>=-0.03 (passes practical bound); nu_h<=1e-10 fails (u_max_final~2.5-3.1, TV~80-120), only nu_h=1e-9 (near RK4 stability ceiling 4e-8) passes. All cases show transient u_max~2.7-3.4 during early bore steepening.
- RATIONALE: The bare stack cannot bound the Burgers self-flux for strong-gradient ICs: the bore physically injects high-k energy faster than dealiasing alone can absorb. Linear viscosity at nu~1e-2-5e-2 matches the Burgers shock-thickness scale; k^8 hyperviscosity needs nu_h near the explicit-stability ceiling to be effective at this Nx.
- RECOMMENDED: Adopt nu_linear=5e-2 as the default u-side dissipation for downstream BKdV runs with bore-like u-gradients (TV_final~9.6, u_min_final>=0). For higher Nx, use implicit/IMEX integration of nu*u_xx (e.g., scipy IMEX-RK or split-step exp(-nu*k^2*dt)) to remove the dt~1/(nu*k_max^2) constraint, and re-test amp/IC sensitivity.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S7_r1
- schema: scope=local_failure | action=retry | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: Gardner-only baseline (m=0 reduction): v_t + 6 v v_x + (3/2) v^2 v_x + v_xxx = 0; IC v_0 = 1.5 sech^2(x+5); Fourier pseudospectral + 2/3 dealias + RK4, Nx=256, L=30, T=10, dt=2e-4. Diagnostics: mass_v, L2v, Gardner H, v_max, n_peaks.
- OBSERVATION: Clean single-peak propagation over T=10: mass_v and L2v conserved to 0.000000%, H drift +0.188%, v_max in [1.4957, 1.5067] (drift -0.137%), n_peaks=1 throughout, phase speed c~3.564 (peak wraps domain twice). No blowup; positive baseline confirmed.
- RATIONALE: Positive baseline, not a failure. sech^2 is an exact KdV soliton and the cubic (3/2)v^2 v_x is a mild perturbation at A=1.5 (cubic/quadratic flux ratio ~A/4=0.375), so radiative shedding stays sub-percent. Establishes that any E2 BKdV breakdown cannot be blamed on Gardner-side instability or numerics.
- RECOMMENDED: Proceed to E2: rerun identical stack under full BKdV (u_t + 3 u u_x = -d_x(3 v^2 + v_xx), v_t + 6 v v_x + v_xxx = -d_x(uv)) with u_0 = v_0^2/2 so m_0=0 to machine precision; track ||m||_L2(t), v_max(t), u_max(t), ||v_BKdV(t)-v_Gardner(t)||_L2 against round1/snapshots.npz.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S7_r2
- schema: scope=regime_bound_failure | action=retry | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: Full BKdV (coupled u,v) with IC v0=1.5*sech^2(x+5), u0=v0^2/2 so m0=0; Fourier pseudospectral Nx=256 L=30, 2/3 dealiasing, RK4 dt=2e-4, T=10. Measured ||m||_L2, v_max, u_max, ||v_BKdV-v_Gardner||_L2 vs round1.
- OBSERVATION: m=0 manifold destroyed on O(1) time: ||m||_L2 reaches 0.74 by t=0.5, 1.22 by t=1, saturates ~2.55. v_max drops 1.498->0.558 (-62.8%), u_max climbs 1.12->3.97, n_peaks 1->8. ||v_BKdV-v_Gardner||_L2 grows to 1.81 (> ||v_BKdV||=0.84). Mass conserved, no blowup.
- RATIONALE: Positive finding: confirms program hypothesis. The m=0 manifold is a kinematic substitution, not a dynamical invariant set of coupled BKdV; the -∂_x(u v) coupling immediately forces m_t off zero, fragmenting the Gardner-stable soliton into a dispersive train while v itself remains bounded (purely physical breakdown).
- RECOMMENDED: Proceed to E3: evaluate the BKdV-S5 algebraic identity m_t|_{m=0}=(v-1)(6 v v_x + v_xxx) on v0(x); compute its L2 norm and FFT spectrum to predict the dominant unstable modes, then compare against early-time m_hat(k,t) from this round's snapshots.npz.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

## BKdV-S7_r3
- schema: scope=local_failure | action=narrow_claim | layer=hypothesis_failure | degree=partial | risk=low_risk_omission | is_trivial=False
- ROUTE: Evaluate BKdV-S5 algebraic source S(x)=(v0-1)(6 v0 v0_x + v0_xxx) for v0=1.5 sech^2(x+5) via Fourier pseudospectral (Nx=256, L=30, 2/3 dealias); compare ||S||_L2, |S_hat(k)|, and A-sweep against round2 m-trajectory.
- OBSERVATION: Predicted growth rate ||S||_L2=1.77/t matches observed ||m||_L2(0.5)/0.5=1.47 within 17%; top-5 amplifying modes (n=4,3,5,2,6) coincide with predicted (n=4,5,3,6,2); spectral cos-sim 0.940; A-sweep loglog slope 0.22 for A in [0.25,0.75], 2.49 for A in [1,2.5], pinpointing the (v-1) sign-flip at A=1.
- RATIONALE: Positive finding: the m_t|_{m=0}=(v-1)(6 v v_x + v_xxx) identity is quantitatively predictive at t<=0.5 because at t=0 it is exact by construction and linear extrapolation t*S is the leading Taylor term; saturation to 0.53 by t=2 reflects nonlinear feedback from accumulated m.
- RECOMMENDED: Extend to A<1 (e.g. A in {0.3, 0.6, 0.9}) where (v-1)<0 over the soliton core and the dispersive piece dominates: rerun the round2 BKdV stack with v0=A sech^2(x+5), u0=v0^2/2, and check whether m-growth scales as predicted slope 0.22 vs the 2.49 regime above A=1.
- TESTED SCOPE: 
- ASSERTED SCOPE: 
- CODE (M/E+/E−/P): 
- numeric evidence fields present? 

