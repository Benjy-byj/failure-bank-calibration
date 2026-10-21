#!/usr/bin/env python3
"""
E1: Burgers bore + KdV soliton interaction
Coupled BKdV system:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx)
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)

Method: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (all explicit)
        No viscosity — baseline to observe bore-steepening behaviour.
"""
import numpy as np
from numpy.fft import fft, ifft, fftfreq
import os

# ── Parameters ────────────────────────────────────────────────────────────────
N   = 256
L   = 30.0          # domain [-15, 15]
T   = 8.0
dt  = 2e-4

x = np.linspace(-15.0, 15.0, N, endpoint=False)

# Wavenumbers (physical frequency in rad/m)
k = 2.0 * np.pi / L * fftfreq(N, d=1.0 / N)   # shape (N,)

# 2/3 dealiasing mask: keep |k_index| <= N//3
k_idx      = np.abs(fftfreq(N) * N)             # |0,1,...,N/2,N/2-1,...,1|
dealias    = (k_idx <= N // 3).astype(float)    # True for kept modes

# Precomputed spectral operators
ik  = 1j * k                  # d/dx in spectral space
ik3 = (1j * k) ** 3           # d^3/dx^3 in spectral space

# ── Initial conditions ────────────────────────────────────────────────────────
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # smoothed bore: u_L=1.5, u_R=0
v = 1.5 / np.cosh(x + 8.0) ** 2            # KdV soliton at x=-8

# ── RHS function ──────────────────────────────────────────────────────────────
def rhs(u, v):
    """Compute (du/dt, dv/dt) for the coupled BKdV system."""
    # --- spectral representation (dealiased) ---
    u_hat = fft(u) * dealias
    v_hat = fft(v) * dealias

    # Dealiased physical fields (used for products to avoid aliasing)
    u_d = ifft(u_hat).real
    v_d = ifft(v_hat).real

    # Derivatives of dealiased fields
    u_x = ifft(ik * u_hat).real
    v_x = ifft(ik * v_hat).real

    # v_xxx in spectral space (linear term, exact)
    v_xxx_hat = ik3 * v_hat

    # Nonlinear products — compute in physical space then FFT + dealias
    uu_x_hat  = fft(u_d * u_x) * dealias    # u * u_x
    vv_x_hat  = fft(v_d * v_x) * dealias    # v * v_x
    uv_hat_nl = fft(u_d * v_d) * dealias    # u * v  (for d_x(u*v))

    # --- RHS ---
    # u_t = -3*u*u_x - d_x(3*v^2 + v_xx) = -3*u*u_x - 6*v*v_x - v_xxx
    du_hat = -3.0 * uu_x_hat - 6.0 * vv_x_hat - v_xxx_hat

    # v_t = -6*v*v_x - v_xxx - d_x(u*v)
    dv_hat = -6.0 * vv_x_hat - v_xxx_hat - ik * uv_hat_nl

    return ifft(du_hat).real, ifft(dv_hat).real

# ── Time integration (RK4) ────────────────────────────────────────────────────
n_steps   = int(round(T / dt))      # 40 000 steps
t_snaps   = np.linspace(0.0, T, 9)  # t = 0, 1, 2, …, 8

snapshots = []
snap_idx  = 0
t         = 0.0

# Save t=0 snapshot
snapshots.append(np.stack([u.copy(), v.copy()]))
snap_idx = 1
print(f"t={t:.3f}: u_max={np.max(u):.4f}, u_min={np.min(u):.4f}, v_max={np.max(v):.4f}", flush=True)

for step in range(n_steps):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u +     dt*k3u, v +     dt*k3v)

    u = u + (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)
    t += dt

    # --- Blow-up guard ---
    if not (np.isfinite(u).all() and np.isfinite(v).all()):
        print(f"NaN/Inf detected at t={t:.4f} (step {step})", flush=True)
        break

    # --- Save snapshot at scheduled times ---
    if snap_idx < len(t_snaps) and t >= t_snaps[snap_idx] - 0.5 * dt:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        print(f"t={t:.3f}: u_max={np.max(u):.4f}, u_min={np.min(u):.4f}, "
              f"v_max={np.max(v):.4f}, v_peak_x={x[np.argmax(v)]:.2f}", flush=True)
        snap_idx += 1

# ── Save output ───────────────────────────────────────────────────────────────
result = np.array(snapshots)          # shape (n_snaps, 2, N)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", result)

print(f"\nDone. Output shape: {result.shape}")
print(f"n_snapshots = {result.shape[0]}")
print(f"Final u_max  = {np.max(np.abs(result[-1, 0])):.4f}")
print(f"Final v_peak = {np.max(result[-1, 1]):.4f}")
print(f"Any NaN?     {np.any(np.isnan(result))}")
