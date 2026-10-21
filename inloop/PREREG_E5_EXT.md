# E5-EXT Preregistration — replicate extension of the gated cells (4 -> 8 reps)

Date: 2026-08-23. Frozen BEFORE any extension run. Ships in the artifact unchanged,
alongside PREREG_E5.md.

## Disclosure of data dependence
This extension is declared AFTER observing the first four replicates of E4 (soft)
and E5 (enforced). The observed 4-rep results: enforced graded 16.8 vs binary 13.8
(exact rank p=0.1286, preregistered primary, direction as predicted); enforcement
cost to binary 19.0->13.8 (p=0.0857, preregistered secondary). The extension is
motivated by power, not by direction-hunting: all preregistered directional
predictions were already met at n=4. To eliminate optional-stopping concerns:

1. Exactly FOUR additional replicates per condition are added, in both the soft
   cell (nomem/binary/graded, reps 4-7) and the enforced cell (binary/graded,
   reps 4-7). NO further extensions will run after this, regardless of outcome.
2. Replicates 0-3 are untouched (per-rep state files; disjoint seed ranges).
3. BOTH reads will be reported in any paper version: the original preregistered
   4-rep read (unchanged) and the pooled 8-rep read, labeled as a declared
   extension.
4. If the pooled primary (enforced graded > enforced binary, exact one-sided
   rank, n=8 vs 8) has p > 0.05, the paper's claims do NOT upgrade: the cell
   remains "directionally consistent, preregistered, modestly powered."
   If p <= 0.05, the text may state the reversal as statistically resolved,
   still reporting both reads.
5. Secondaries as in PREREG_E5.md: enforcement cost to binary (soft vs enforced,
   now 8 vs 8); graded invariance under enforcement; mechanism signatures
   (strict rescues under enforced binary = 0; train-while-locked = 0; budget
   identity exact) must hold on the new replicates as on the old.
6. Analysis code unchanged (e5_analysis.py, rank tests exact).

## Command
the extension run target
(resumes reps 0-3 as complete; runs reps 4-7 fresh in both cells; reruns analysis)
