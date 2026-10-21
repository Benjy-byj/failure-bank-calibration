"""Clean-limit constants kappa_v(rho) for verification-stage wrongful convictions (App. C)."""
import numpy as np
rng = np.random.default_rng(0); us = np.linspace(-6, 6, 241)
for v in (1, 2, 3, 4):
    Z = rng.standard_normal((1_500_000, v + 1))
    R = np.array([np.mean((Z[:, 0] > -u) & (Z.mean(1) < -u)) for u in us])
    Ip = np.trapezoid(R[us >= 0], us[us >= 0]); Im = np.trapezoid(R, us) - Ip
    print(f"v={v}: kappa(1)={Ip/(Ip+Im):.3f}", " ".join(f"kappa({r})={r*Ip/(r*Ip+Im):.3f}" for r in (0.5, 2.0)))
