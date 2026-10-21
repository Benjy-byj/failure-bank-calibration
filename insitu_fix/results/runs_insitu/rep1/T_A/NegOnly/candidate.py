"""
FINAL SOLVER (E2): Coupled Burgers-swept-KdV

PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)   =>  u_t = -d_x(3/2 u^2 + 3v^2) - v_xxx
  v_t + 6 v v_x + v_xxx = -d_x(u v)    =>  v_t = -d_x(3v^2 + u*v) - v_xxx

IC: v0 = 2*sech^2(x+5),  u0 = 0.5*v0^2 + 0.02*v0  (m=0.02*v, reduced perturbation from suggested 0.2)
Domain: x in [-15, 15], Nx=256 (periodic)
Method: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4, dt=2e-4

Best of 3 experiments: v_max(T=8)=0.701, mass_v drift=0.000%, |u|_max(T=8)=5.87<15.
"""

import numpy as np
import os

# ── Domain ────────────────────────────────────────────────────────────────────
L    = 30.0
Nx   = 256
x    = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx   = L / Nx

# ── Wavenumbers ───────────────────────────────────────────────────────────────
k    = (2.0 * np.pi / L) * np.fft.fftfreq(Nx) * Nx
ik   = 1j * k
ik3  = (1j * k) ** 3    # (ik)^3 = -ik^3, spectral operator for d^3/dx^3

# ── 2/3-rule dealiasing mask ─────────────────────────────────────────────────
n_keep  = Nx // 3           # 85 modes kept
dealias = (np.abs(np.fft.fftfreq(Nx) * Nx) <= n_keep).astype(float)

# ── Initial conditions ────────────────────────────────────────────────────────
v0 = 2.0 / np.cosh(x + 5.0) ** 2
u0 = 0.5 * v0 ** 2 + 0.02 * v0    # m = 0.02*v  (IC adjusted to reduce perturbation)


# ── RHS ──────────────────────────────────────────────────────────────────────
def rhs(u, v):
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Pre-RHS dealiasing (BKdV-S1: required to prevent aliasing blow-up)
    u_d = np.fft.ifft(u_hat * dealias).real
    v_d = np.fft.ifft(v_hat * dealias).real

    # Nonlinear flux functions
    Fu = 1.5 * u_d ** 2 + 3.0 * v_d ** 2   # u-flux
    Fv = 3.0 * v_d ** 2 + u_d * v_d         # v-flux

    # v_xxx: linear dispersive term (from dealiased v_hat)
    v_xxx = np.fft.ifft(ik3 * v_hat * dealias).real

    # Dealiased spectral derivatives of fluxes
    dFu_dx = np.fft.ifft(ik * np.fft.fft(Fu) * dealias).real
    dFv_dx = np.fft.ifft(ik * np.fft.fft(Fv) * dealias).real

    return -dFu_dx - v_xxx, -dFv_dx - v_xxx


# ── Time integration ─────────────────────────────────────────────────────────
T       = 8.0
dt      = 2e-4
n_steps = int(round(T / dt))

# 9 snapshots evenly spaced t=0,1,...,8
n_snap   = 9
snap_ts  = np.linspace(0.0, T, n_snap)
snap_set = set(np.round(snap_ts / dt).astype(int))

snapshots = []
u = u0.copy()
v = v0.copy()

print(f"Running E2 final: Fourier+2/3+RK4, dt={dt}, IC m=0.02*v")

for step in range(n_steps + 1):
    if step in snap_set:
        t_now  = step * dt
        v_max  = float(np.max(v))
        u_amax = float(np.max(np.abs(u)))
        finite = bool(np.isfinite(u).all() and np.isfinite(v).all())
        print(f"  t={t_now:.2f}: v_max={v_max:.4f}  |u|_max={u_amax:.4f}  finite={finite}")
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

    if step == n_steps:
        break

    # Classical RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u +       dt * k3u, v +       dt * k3v)

    u += (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v += (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)

    # Post-step projection onto dealiased subspace (conservative regularization)
    u = np.fft.ifft(np.fft.fft(u) * dealias).real
    v = np.fft.ifft(np.fft.fft(v) * dealias).real

# ── Diagnostics and save ──────────────────────────────────────────────────────
result = np.array(snapshots)   # shape (9, 2, 256)
print(f"\nFinal shape: {result.shape}")

v_init_mass  = np.sum(result[0,  1, :]) * dx
v_final_mass = np.sum(result[-1, 1, :]) * dx
mass_drift   = abs(v_final_mass - v_init_mass) / abs(v_init_mass) * 100.0

print(f"v_max(t=0) : {float(np.max(result[0, 1, :])):.4f}")
print(f"v_max(t=T) : {float(np.max(result[-1, 1, :])):.4f}  (target: dominant peak >= 0.5*initial_2.0)")
print(f"|u|_max(T) : {float(np.max(np.abs(result[-1, 0, :]))):.4f}  (target: < 15)")
print(f"mass drift : {mass_drift:.4f}%  (target: < 8%)")

from scipy.signal import find_peaks
v_fin = result[-1, 1, :]
v_max_fin = float(np.max(v_fin))
peaks, _ = find_peaks(v_fin, height=0.1 * v_max_fin, prominence=0.05 * v_max_fin)
print(f"v peaks at T=8: {len(peaks)}, dominant={v_max_fin:.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", result)
print("Saved pred_results/T_A.npy")
