char-GPT live-loop replay analysis (36 mutations, 216 verdict events, 16-seed truth).
- `log.jsonl` / `ext_log.txt`: raw verdict + ground-truth records from the A100 loop.
- `summary.json`: per-mutation summary.
- `replay_analysis.py`: W_A/W_B, measurement-aware estimators, cluster bootstrap.
- `loo.py`, `loo_check.py`: leave-one-out empirical-prior predictions.
- `replay_analysis.py` covers the pooled/extension analysis (W_A, W_B, cluster bootstrap).
- `replay_fig2.py`: Fig. 3 (appendix) generator.
The training-side driver (mutation schedule + nanoGPT-style loop) is not included
in this review package. The verdict protocol it implements is fully specified in
the manuscript: single-seed ratchet against a 24-seed baseline, 2-seed
verification, 16-seed ground truth. The logs above are its complete output.
