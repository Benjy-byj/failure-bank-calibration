# End-to-end cumulative research loop: do failure banks actually cost discoveries?

This is the missing causal link: not a simulation, a real cumulative research loop where
ideas are COMPOSABLE config patches (a confirmed idea spawns children = parent + one more
mutation, i.e. success-gated supply) and every verdict is a real MLP training run.
Four memory policies run on the SAME cached noise realizations (paired comparison):

    none | binary (today's shared failure bank) | threshold (P(dead)>0.8) | parole (binary + 5%)

Metric: TRUE discoveries within a fixed budget (confirmed ideas whose held-out multi-seed
ground truth beats the incumbent), plus lineage depth reached.

## Reference result (low-noise regime)
sigma/tau = 0.24, budget 80: binary 18.0, parole 17.5, threshold 16.0, none 14.2 true discoveries
(4 paired seeds). Binary WINS here. This is what the theory predicts for a clean, short-horizon
loop -- it is the monotone (left) side of the inverted U, and it is the falsification test that
the harm claim must survive. The decisive experiment is the noisy, long-horizon cell.

## Run this (a few minutes each on an A100-class box; CPU-only, sklearn)
    pip install scikit-learn scipy numpy
    NOISE=high BUDGET=200 python loop.py 3600 8      # the decisive cell
    NOISE=high BUDGET=80  python loop.py 3600 8      # noise alone
    NOISE=low  BUDGET=200 python loop.py 3600 8      # horizon alone
    NOISE=low  BUDGET=80  python loop.py 3600 8      # replicates the reference cell

Each writes results_{NOISE}_b{BUDGET}.jsonl (resumable; rerun the same command after any stop).
Each cell writes a .jsonl of per-run records for analysis.

Args: first = wall-clock seconds before it stops cleanly, second = number of replicate seeds.
