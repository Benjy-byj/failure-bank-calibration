# PREREG_BX — Behavioral trial extension (declared before any extension call)

Date: 2026-08-23. Frozen before data collection; ships in the artifact unchanged,
alongside PREREG_E5.md and PREREG_E5_EXT.md.

## Motivation and disclosure
Reviewer-facing weakness: behavioral cells run 5–6 trials per model-condition.
This extension doubles the trial count in the cells that carry headline claims.
It is declared AFTER the original results are known; the direction of every
extended cell is therefore known in advance. The purpose is precision, not
direction-hunting. Discipline mirrors the E5 extension:
1. Exactly +6 trials per condition per model in the targeted cells; NO further
   behavioral extensions after this, regardless of outcome.
2. Completed trials are untouched: the extension appends to each model's log
   with plan-prefix alignment (verified) and absolute-index seeds.
3. BOTH reads are reported in any paper version: original counts (unchanged)
   and pooled counts, labeled as a declared extension.
4. Risk acceptance, stated now: pooled counts may weaken current headlines
   (e.g., a first DEAD revisit, a disclaimer repair that regresses). Whatever
   the pooled data show is reported. Zero-count claims (e.g., 0/94-style)
   become k/N with exact CP bounds either way.
5. No model or provider is added or dropped; provider-default serving as before;
   prompts verbatim (the code paths are unchanged—only trial counts grow).

## Targeted cells (per model, 9 non-Claude models unless noted)
- F2 ML-domain choice: DEAD and DEAD+disclaimer, 6 -> 12 each
  (powers: per-family choice suppression; the one-family disclaimer repair,
  currently DeepSeek-R1 4/5).
- F3 override directive: 6 -> 12 (currently 40/49 vs 7/48 pooled).
- Chem choice flip: DEAD and INCONCLUSIVE, 6 -> 12 each (powers the
  second-domain flip, currently 12/43 vs 50/50, and the family sign test's
  chem arm).
- If the original ML-domain INCONCLUSIVE choice arm's runner (task F in the
  original crossfam script) is available locally, extend it identically
  (6 -> 12); if not, the ML INCONCLUSIVE arm remains at original n and this is
  stated. [Runner not present in this package; check iclr3/iclr4 dirs.]

## Analysis (fixed now)
- Pooled per-family counts with exact two-sided Fisher per family where n
  permits; the family-level sign test remains the design-robust headline.
- 0-count cells: exact one-sided 95% Clopper-Pearson upper bounds at pooled N.
- No new hypotheses; no subgroup analyses beyond the per-family reporting the
  paper already does.

## Commands (per model; resume-safe, append-only)
python3 crossfam_f2.py --provider P --model M --tasks f2   --n-ext 6
python3 crossfam_f2.py --provider P --model M --tasks f3   --n-ext 6
python3 crossfam_f2.py --provider P --model M --tasks chem --n-ext 6
(--plan-only prints the trial plan without API calls; prefix alignment is
verified in the shipped package.)

## Post-run deviation log (2026-08-23, after data receipt)
1. The extension attached to a fresh base run rather than the original study's
   logs (the run directory did not contain them). The full 24-trial files are
   therefore reported as an INDEPENDENT REPLICATION, never pooled with the
   original study; both studies' numbers appear in the paper.
2. The F3 arm did not execute: f3 shared the f2 log file, so the extended f2
   line count made the resume logic skip the entire f3 plan (harness bug, now
   fixed: f3 writes f3_{tag}.jsonl). F3 remains at its original n; this is
   stated in App. B.
3. Everything else ran as registered; per-family counts in App. B.
