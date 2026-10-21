"""
E1: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (fully explicit)
PDE: Coupled Burgers-swept-KdV
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx)
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)
IC: v = 4*exp(-((x+5)^2)/2.25), u = 0
Domain: x in [-15, 15], periodic, Nx=256
T = 6.0, dt = 1e-4
"""

import numpy as np
import os
import sys

# ── Grid ──────────────────────────────────────────────────────────────────────
Nx = 256
L = 30.0
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)   # x in [-15, 15)
dx = L / Nx

# ── Wavenumbers ───────────────────────────────────────────────────────────────
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)           # angular freq [rad/unit]

# ── 2/3 dealiasing mask ───────────────────────────────────────────────────────
ki = np.fft.fftfreq(Nx) * Nx                          # integer freq indices
dealias = (np.abs(ki) <= Nx // 3).astype(float)       # keep |k_idx| <= 85

# Pre-compute k^3 for the dispersive term
k3 = k ** 3

# ── Initial conditions ────────────────────────────────────────────────────────
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# ── Time parameters ───────────────────────────────────────────────────────────
dt = 1e-4
T = 6.0
n_steps = int(round(T / dt))   # 60 000 steps

# ── Snapshot storage ──────────────────────────────────────────────────────────
n_snaps = 10
snap_ts = np.linspace(0.0, T, n_snaps)
snaps = np.zeros((n_snaps, 2, Nx))
snaps[0, 0] = u.copy()
snaps[0, 1] = v.copy()
snap_idx = 1


# ── RHS function ──────────────────────────────────────────────────────────────
def rhs(u, v):
    """Compute (du/dt, dv/dt) for the coupled Burgers-swept-KdV system."""
    uh = np.fft.fft(u)
    vh = np.fft.fft(v)

    # Dealiased spectral coefficients
    uh_d = uh * dealias
    vh_d = vh * dealias

    # Dealiased physical fields
    u_d = np.fft.ifft(uh_d).real
    v_d = np.fft.ifft(vh_d).real
    ux  = np.fft.ifft(1j * k * uh_d).real
    vx  = np.fft.ifft(1j * k * vh_d).real

    # Dispersive term (shared): fft(v_xxx) = (ik)^3 * vh_d = -ik^3 * vh_d
    vxxx_h = (-1j * k3) * vh_d

    # Nonlinear products – dealiased after each multiplication
    u_ux_h = np.fft.fft(u_d * ux) * dealias     # fft(u * u_x), dealiased
    v_vx_h = np.fft.fft(v_d * vx) * dealias     # fft(v * v_x), dealiased
    uv_h   = np.fft.fft(u_d * v_d) * dealias    # fft(u * v),   dealiased
    uv_x_h = 1j * k * uv_h                       # fft((u*v)_x) = ik * fft(u*v)

    # u RHS: u_t = -3*u*u_x  -  6*v*v_x  -  v_xxx
    #  (from: u_t + 3*u*u_x = -d_x(3v^2 + v_xx) = -6*v*v_x - v_xxx)
    u_rhs_h = -3.0 * u_ux_h - 6.0 * v_vx_h - vxxx_h

    # v RHS: v_t = -6*v*v_x  -  v_xxx  -  (u*v)_x
    v_rhs_h = -6.0 * v_vx_h - vxxx_h - uv_x_h

    u_rhs = np.fft.ifft(u_rhs_h).real
    v_rhs = np.fft.ifft(v_rhs_h).real
    return u_rhs, v_rhs


# ── RK4 time integration ──────────────────────────────────────────────────────
print(f"Starting RK4:  Nx={Nx}, dt={dt}, T={T}, n_steps={n_steps}")
print(f"IC  v_max={v.max():.4f}, mass_v={np.sum(v)*dx:.4f}")

for step in range(n_steps):
    # Classical RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,      v + dt*k3v)

    u += (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v += (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)

    t_now = (step + 1) * dt

    # Save snapshots
    while snap_idx < n_snaps and t_now >= snap_ts[snap_idx] - 1e-12:
        snaps[snap_idx, 0] = u.copy()
        snaps[snap_idx, 1] = v.copy()
        snap_idx += 1

    # Early NaN check at steps 100, 1000, 10000
    if step in (99, 999, 9999):
        if not np.all(np.isfinite(v)) or not np.all(np.isfinite(u)):
            print(f"NaN/Inf detected at step {step+1}!  Aborting.")
            sys.exit(1)
        t_chk = (step + 1) * dt
        print(f"  step {step+1:6d}  t={t_chk:.4f}  v_max={v.max():.4f}  u_max={abs(u).max():.4f}")

# ── Ensure final snapshot ─────────────────────────────────────────────────────
snaps[-1, 0] = u
snaps[-1, 1] = v

# ── Diagnostics ───────────────────────────────────────────────────────────────
v_fin = snaps[-1, 1]
u_fin = snaps[-1, 0]
mass_v0 = np.sum(snaps[0, 1]) * dx
mass_vT = np.sum(v_fin) * dx
drift_pct = abs(mass_vT - mass_v0) / abs(mass_v0) * 100.0

print(f"\n=== Final diagnostics ===")
print(f"all_finite : {np.all(np.isfinite(snaps))}")
print(f"v_max      : {v_fin.max():.4f}")
print(f"v_min      : {v_fin.min():.4f}")
print(f"u_max      : {abs(u_fin).max():.4f}")
print(f"mass_v  IC : {mass_v0:.6f}")
print(f"mass_v   T : {mass_vT:.6f}")
print(f"mass drift : {drift_pct:.4f}%")

# Count peaks with amplitude >= 0.8
from scipy.signal import find_peaks
peaks, props = find_peaks(v_fin, height=0.8, distance=8)
print(f"\nPeaks in v >= 0.8 : {len(peaks)}")
for i, p in enumerate(peaks):
    print(f"  peak {i+1}: x={x[p]:.3f}, amp={v_fin[p]:.4f}")

# ── Save output ───────────────────────────────────────────────────────────────
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', snaps)
print(f"\nSaved pred_results/T_B.npy  shape={snaps.shape}")
