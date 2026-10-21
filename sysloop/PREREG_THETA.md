# PREREG_THETA — threshold sensitivity of the end-to-end advantage (frozen before running)
Date 2026-09-12. Question (reviewer): does the +30–32% of evidence-graded memory persist across a
reasonable range of the lock threshold θ*? Design: the recorded 8-replicate loop, graded rule at
θ ∈ {0.6, 0.7, 0.9, 0.95} (recorded run = 0.8), 8 replicates each, fresh seed namespaces, truth values
preserved for all previously known configs (only new configs truth-tested, 970k namespace).
Report: per-θ discoveries, one-sided exact rank test vs binary (46.6) for each θ, and vs θ=0.8.
Read: the advantage is robust if every θ in [0.6, 0.95] beats binary at p≤0.05; θ→1 is expected to
degrade (over-churn, as in simulation). Both outcomes reported; no further sweeps.
