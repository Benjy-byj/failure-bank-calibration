Core model + all simulation experiments.
- `sim_core.py` / `sim_v3.py`: the cumulative-research model (success-gated supply, verdict pipeline, deference knob s).
- `scan_AB.py` → scan_AB.json: inverted-U across noise regimes (Fig. 1).
- `phase_theory.py` → phase.json, lambda.json: phase diagram + λ=1 contour.
- `horizon.py` → horizon.json: losses vs budget, ordered by extinction probability.
- `rulefam.py`, `robust.py`, `boost.py`: design-rule family comparison (threshold vs matching vs parole), misspecification robustness.
All scripts resolve their data files relative to the repository, so they can be run
from any working directory. Each regenerates its own JSON; the committed JSONs let
you skip recomputation. `boost.py` reads the char-GPT replay logs from
`../replay_chargpt/`. Figures are written to `figures_out/` at the repository root.
