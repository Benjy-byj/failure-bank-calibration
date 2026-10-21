# PREREG_P3 — Rate-matched parole control (frozen before any run)
Date: 2026-08-23. Motivation: reviewers can attribute graded's +30% to retry VOLUME
(graded retries open records freely; parole reopens at a fixed 5%) rather than
CALIBRATION (which records to retry). This control matches the volume.

Design: (1) deterministically replay the 8 recorded graded loops (identical rng
stream, cached training) counting encounters of recorded configs and reopens
(filter passes) -> pooled per-encounter reopen rate r*. (2) Run parole_matched:
identical to parole but reopen probability = r* per encounter, 8 replicates,
fresh seed namespace (700k), same budget/landscape. (3) Truth values for
previously-known configs are PRESERVED from the recorded run (the original
script's index-dependent truth seeds would silently shift published values);
only new configs are truth-tested (6 seeds, 950k namespace).

Hypotheses (decision rule = exact one-sided rank test, 8v8):
- H1 (calibration matters): graded (60.5±4.8) > parole_matched; p and point gap
  reported; if p<=0.05 the paper may state "volume-matched parole remains
  inferior: the gain is calibration, not volume."
- H2 (volume explains): parole_matched within noise of graded (p>0.2 and gap
  <1 discovery) -> the paper's calibration framing must be revised; this file
  is cited when we do.
- Secondary: parole_matched vs plain parole (does volume alone help at all?).
Whatever lands is reported; no further conditions after this one.
