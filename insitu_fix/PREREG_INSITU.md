# PREREG_INSITU — Calibrated-scope rendering inside a deployed failure bank (frozen before any run)

Date: 2026-09-11. System: [1] hch-wang/Negative_Knowledge, reproduction/section4 (their stage-2 runner,
their model choice, their prompts, their verified phenomenon checks). We change ONE thing.

## Intervention (NegCal)
The 43 negative-bank entries are served verbatim; each gains a `status` line derived from the entry's
own `failure.scope` field (spec rules 3–5): general_failure with abandon/change action → CLOSED (6);
regime_bound/local, deep syntheses, and evidence-free entries → OPEN (37). The preface "Entries describe
methods/regimes that FAILED. Use to avoid pitfalls" becomes the calibrated instruction (OPEN = advisory
outside its regime; do not rule out a method class on an OPEN entry alone). Diff vs NegOnly: 45 lines.

## Design
Tasks T_A, T_B, T_C × conditions NegOnly, NegCal × k replicates (target k=5, floor k=3) plus NoKB × 2
replicates as a reference (amended before any run, 2026-09-11, to save cost; the k actually completed is
reported, no extension). API temperature = their default. Outcome = their
verified phenomenon check (`useful`), unchanged.

## Hypotheses (decision rules fixed now)
- H1 (primary): pooled useful-rate NegCal > NegOnly (exact one-sided Fisher on 3k vs 3k).
- H2: on T_A (where their released run shows the bank hurting) NegCal recovers NoKB-level success;
  on T_B/T_C NegCal keeps NegOnly's gain (no significant loss).
- H0 read: NegCal ≈ NegOnly → scope rendering alone does not help; the paper reports it as such and the
  audit's consumption-collapse finding stays descriptive.
Both directions are reported. This is a prompt-level, evidence-free rendering (the records have no
numeric evidence), so it tests rules 3–5 of the spec, not the full evidence-graded lock.

## Reporting
Per-cell useful table, pooled rates, exact tests, and every reasoning.md released.

## Results and deviation log (2026-09-12, after data receipt)
Deviations (all before/independent of outcomes): (1) executed via headless Claude Code (the authors' own
stage-2 protocol per meta.json tools_allowed) rather than the API dispatcher — model = current Sonnet via
the CLI, so cross-version comparison to the released 2026 runs is NOT clean; within-experiment comparisons
are; (2) NoKB reduced to 2 replicates for cost (amended pre-run); (3) the authors' absolute paths in
saved prompts were localized identically for every condition.
Outcome (independently recounted from .npy with phenomenon_checks; 0 mismatches):
  T_A  NoKB 2/2  NegOnly 4/5  NegCal 2/5 | T_B 2/2 4/5 5/5 | T_C 2/2 5/5 5/5
  pooled NoKB 6/6, NegOnly 13/15, NegCal 12/15; H1 one-sided Fisher p = 0.835 → NOT SUPPORTED.
  Deference readout (research_state.jsonl + reasoning.md, 15 cells each): bank rejections 67 → 57,
  citations 29 → 34, status-field references 0 → 27.
Read: prompt-level scope calibration shifts stated deference, not outcomes; outcomes at ceiling for a
current model; the released single-run "bank hurts on T_A" does not replicate (NegOnly 4/5).
