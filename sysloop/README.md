End-to-end closed-loop system experiment (four memory conditions, real training runs).
`python sysloop.py 600` runs/resumes; results/cache.jsonl contains all 4,866 cached
(config,seed)->loss entries, so the full comparison replays deterministically in
seconds without re-training. `sysfig.py` regenerates the appendix figure.
Conditions: no-memory / binary DEAD / evidence-graded (P(dead)>0.8, pooled) / parole 5%.
