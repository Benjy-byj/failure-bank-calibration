# E5 Preregistration — Enforced-lock LLM cell (written before data collection)

Date: 2026-08-23. Author of record: the paper's authors. This document is frozen before
any E5 API call is made; it ships in the released artifact unchanged.

## Motivation

E4 (success-gated LLM cell, 4 replicates) found the binary–graded ordering of the
algorithmic end-to-end loop (graded 60.5 vs binary 46.6, p<1e-3 at 8 replicates)
does **not** reproduce under a deployed LLM proposer whose deference is behavioral:
nomem 11.5±5.7 / binary 19.0±3.6 / graded 15.8±5.6. The paper's interpretation:
the LLM's soft deference (22% in-loop override rate) acts as unmanaged parole,
quietly self-repairing binary's wrongful convictions (10 rescues under binary),
while graded's invited retries cost scarce frontier slots. This interpretation is
currently an inference from mechanism-level bookkeeping, not a causal isolation.

E5 closes the 2×2: {proposer: algorithmic, LLM} × {lock: structural, behavioral}.
The missing cell is **LLM proposer + code-enforced lock**.

## Design

`llm_loop.py --hard --gated --enforce`, budget 150, 4 replicates, conditions
binary and graded (nomem has nothing to enforce; parole out of scope). Same
landscape, grid, baseline, and truth-validation protocol as E4.

Enforcement semantics (mirroring the algorithmic loop's structural lock):
- A proposal whose bank status is DEAD (binary) or CLOSED, i.e. P(dead)>0.8
  (graded), is blocked **before** it can run: no training, no budget cost.
- The model is told of the block and re-prompted (the enforcement rule is also
  stated in the prompt up front — no deception).
- Three consecutive blocked proposals forfeit one budget slot (deadlock escape);
  forfeits are logged (`enforce_forfeits`), blocked attempts are logged
  (`enforce_blocks`, `blocked` key list).
- Under graded, OPEN records (P(dead)≤0.8) remain proposable — that is the
  schema's design; only the lock is enforced.
- Enforcement is checked before the supply gate; gate semantics are unchanged
  from E4 (violations forfeit the slot).

## Hypotheses and decision rules (fixed now)

**H1 (paper's interpretation — soft deference erodes the graded edge).**
Prediction: under enforcement, graded > binary re-emerges.
- Primary read: direction of the point estimates (4 replicates give limited
  power; we will report the exact one-sided rank test p and will NOT claim
  significance it does not have).
- Causal signature (must hold if enforcement works as intended): rescues under
  enforced binary = 0 by construction (verified from state files); binary's
  wrongful stock can only grow; graded's rescues persist via OPEN records.
- Secondary prediction: enforced binary ≤ soft binary (removing self-repair
  should not help binary).

**H2 (alternative — the retry-cost mechanism dominates).**
Prediction: graded ≤ binary even under enforcement.
Consequence if observed: the paper's E4 interpretation is wrong or incomplete;
the Sec. 5 explanation and the "danger concentrates where banks are enforced"
framing must be revised before any camera-ready, and this preregistration will
be cited when we do so.

**Ambiguity rule.** If directions agree with H1 but overlap is large
(one-sided rank p > 0.2), we report the cell as directionally consistent and
underpowered, and do not upgrade the paper's claims.

No outcome will be omitted from the artifact.

## Cost estimate

Same cell as E4: the shared training cache covers most (config, seed) pairs;
expected marginal compute is dominated by ~8 loops × ~150 proposal calls of
API traffic plus truth-validation of newly-distinct configs (4 seeds each).
