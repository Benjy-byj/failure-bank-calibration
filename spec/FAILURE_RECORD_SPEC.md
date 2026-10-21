# Failure-record specification (calibrated conviction), v1

A minimal, adoptable schema for negative results in shared research memory. Design goal:
a verdict that carries its own evidence and can be challenged — lossy in authority, not in evidence.
Everything below is what our experiments identify as load-bearing; everything else is optional.

## Required fields
| field | type | meaning |
|---|---|---|
| `config` | object | the exact attempt (params, code hash, data hash) — retrieval key |
| `n` | int | number of independent runs behind the verdict |
| `estimate` | float | observed effect vs. the relevant baseline (same units as the pipeline's metric) |
| `sigma` | float | run-to-run noise of the pipeline at this config (measured, not assumed) |
| `p_dead` | float | P(true effect ≤ 0 \| evidence) — the one-step Bayes posterior from (n, estimate, sigma) and the pipeline's effect prior |
| `status` | enum | `OPEN` (p_dead below threshold θ*) or `CLOSED` (p_dead ≥ θ*) |
| `evidence_refs` | list | pointers to raw run logs / seeds so a consumer can recompute p_dead |

## Rules
1. **Lock only on evidence**: `CLOSED` iff `p_dead ≥ θ*`, with θ* = c/V (cost of a retry over value of a rescued idea); our operating point θ* ≈ 0.8. Verification-stage near misses (large sigma, small n) rarely clear θ* and stay `OPEN`.
2. **Every record is reopenable**: a new run appends to `evidence_refs`, updates (n, estimate, sigma, p_dead) and may flip `status`. There is no terminal state.
3. **Consumers read `status`, not prose**: prompts/enforcement act on `OPEN`/`CLOSED`; free-text diagnoses are advisory and must never be the sole basis for pruning.
4. **Scope is a field, not a sentence**: if a verdict is regime-bound, record the tested regime as `config` ranges; a consumer outside that range treats the record as `OPEN` by default.
5. **No verdict without n ≥ 1 and sigma**: a record lacking noise cannot be `CLOSED`.

## What this fixes, by measured failure mode
- Wrongful conviction at marginal effects (10–50% of verdicts in our loops): `p_dead` prices the noise instead of a binary label.
- Behavioral lock (agents defer to DEAD against their beliefs, 9/9 families): consumers act on `status`, and `OPEN` invites retrial.
- Lineage extinction under success-gated supply: rule 2 restores the one activity (independent retrial) that exonerates.
- Category error observed in the wild (positive findings typed as failures): `status` derives from `p_dead`, not from a curator's categorical guess.

## Plug-in estimation
`sigma`: from any repeated run the pipeline already performs (our replays estimate it from logs). Effect prior: the pipeline's own logged effect distribution. Both are re-estimable from the bank itself; no new instrumentation.

## Compatibility
A categorical schema (layer/scope/action) can keep its fields; add the seven above. A bank that
already grades scope is half-way there (see audit/): it needs the evidence fields and rule 2.
