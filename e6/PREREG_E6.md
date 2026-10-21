# PREREG_E6 — Second-family replication of the success-gated, code-enforced LLM cell (frozen before any run)
Date 2026-09-12. Purpose: the paper's deployed-LLM causal result (enforced graded > enforced binary, DeepSeek,
8 replicates, p=0.021) has one proposer family. This is a NEW preregistered study on a second family, not an
extension of E5 (PREREG_E5_EXT's hard stop is honoured: no DeepSeek cell is touched or pooled).
Design: proposer GPT-4o (OpenRouter, default sampling), marginal landscape (--hard), success-gated supply
(--gated), budget 150, 12 replicates per condition. Soft cell: nomem / binary / graded (bank in-prompt).
Enforced cell: binary / graded (--enforce; nomem is undefined under enforcement). Same harness, truth
preserved across resumes, event logs on.
Hypotheses (decision rules fixed now; exact one-sided rank tests, 12 v 12):
- H1 (primary): enforced graded > enforced binary in truth-validated discoveries; p<=0.05 = replicated.
- H2 (structure): soft cell shows no graded advantage (as in DeepSeek); enforced cell shows the reversal.
- H3 (mediation, descriptive): under enforced binary, strict rescues = 0 and wrongful-locked stock > 0 with
  blocked retries > 0; under enforced graded, rescues > 0 via OPEN records — the chain
  binary bank -> wrongful good ideas locked -> rescues down -> discoveries down, in the second family.
Both directions reported; if H1 fails the paper says the ordering is family-contingent. No extension
beyond 12 replicates. Cost estimate: 60 loops x 150 calls ~ 9k GPT-4o calls; run soft then enforced
(shared training cache — do not run the two invocations concurrently; within an invocation, replicate loops
run concurrently via --par with a lock-protected cache; loop trajectories are unaffected by parallelism).

## Results (2026-09-12, after data receipt; independently recounted from state files, 0 mismatches)
Soft: nomem 3.7±2.2, binary 9.1±2.3, graded 10.1±2.9 (bank vs none p=1.7e-5 both; graded vs binary p=0.17).
Enforced: binary 13.4±4.6 [20,2,17,15,14,12,13,16,13,15,8,16], graded 12.2±1.7 [10,11,11,10,13,13,11,12,13,14,14,15].
H1 (graded > binary): p = 0.961 -> NOT SUPPORTED; binary ahead at p = 0.050. Enforcement raises binary (p=0.001) and graded (p=0.034).
H2: soft shows no significant graded advantage (as in DeepSeek); the enforced REVERSAL does not replicate.
H3: mechanism signature identical to DeepSeek — strict rescues under enforced binary 0, wrongful stock 54, 418 blocked
retries, 40 forfeits; graded 24 rescues via OPEN; train-while-locked 0; budget identity exact (24/24).
Read: GPT-4o's bankless failure mode is repetition (12–25 distinct configs per loop); the enforced lock's efficiency
gain (distinct 35 -> 52) outweighs its fertility loss at budget 150. The DeepSeek reversal is family-contingent;
the mechanism is not. Reported in the paper as such. Runs used --par 8 (threads); trajectories unaffected.
