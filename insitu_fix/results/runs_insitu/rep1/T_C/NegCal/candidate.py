"""
E3: Same as E2 but nu_u=1e-2 (minimum sufficient viscosity per BKdV-S6).
Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (explicit),
    dt=1e-4, linear viscosity nu=1e-2 on u-equation.

Coupled Burgers-swept-KdV:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)   => u_t = -3/2*d_x(u^2) - 3*d_x(v^2) - v_xxx + nu*u_xx
  v_t + 6 v v_x + v_xxx = -d_x(u v)    => v_t = -3*d_x(v^2) - v_xxx - d_x(u*v)

Domain: x in [-15, 15], Nx=256, T=8.0, dt=1e-4, nu_u=1e-2
"""

import numpy as np
from numpy.fft import fft, ifft, fftfreq
import os
from scipy.signal import find_peaks

# Domain
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
k = 2.0 * np.pi * k_idx / L

# 2/3-rule dealiasing mask
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(float)

# Viscosity on u-equation
nu_u = 1e-2

# Initial conditions
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v = 1.5 / np.cosh(x + 8.0)**2

# Time parameters
T = 8.0
dt = 1e-4
n_steps = int(round(T / dt))

# Snapshot times
n_snaps = 9
snap_times = np.linspace(0.0, T, n_snaps)
snap_indices = set(int(round(t / dt)) for t in snap_times)
snap_indices.add(0)
snapshots = []

def dealias(f_hat):
    return f_hat * dealias_mask

def rhs(u, v):
    v_hat = fft(v)
    u_hat = fft(u)

    u2_hat = dealias(fft(u * u))
    v2_hat = dealias(fft(v * v))
    uv_hat = dealias(fft(u * v))

    ik = 1j * k
    ik3 = (1j * k)**3

    # viscosity
    visc_u_hat = -nu_u * k**2 * u_hat

    du_hat = -1.5 * ik * u2_hat - 3.0 * ik * v2_hat - ik3 * v_hat + visc_u_hat
    dv_hat = -3.0 * ik * v2_hat - ik3 * v_hat - ik * uv_hat

    du = np.real(ifft(du_hat))
    dv = np.real(ifft(dv_hat))
    return du, dv

snapshots.append((u.copy(), v.copy()))
blow_up_step = None

for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)

    u = u + (dt / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2*k2v + 2*k3v + k4v)

    if step in snap_indices:
        snapshots.append((u.copy(), v.copy()))

    if not np.isfinite(u).all() or not np.isfinite(v).all():
        blow_up_step = step
        print(f"BLOW-UP at step {step}, t={step*dt:.4f}")
        break

    if step % 20000 == 0:
        print(f"  t={step*dt:.2f}, u_max={u.max():.3f}, v_max={v.max():.3f}")

while len(snapshots) < n_snaps:
    snapshots.append(snapshots[-1])
snapshots = snapshots[:n_snaps]

out = np.zeros((n_snaps, 2, Nx))
for i, (ui, vi) in enumerate(snapshots):
    out[i, 0, :] = ui
    out[i, 1, :] = vi

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)
print(f"Saved pred_results/T_C.npy, shape={out.shape}")

print(f"\n--- Diagnostics ---")
u_fin = out[-1, 0, :]
v_fin = out[-1, 1, :]
print(f"u_max={u_fin.max():.4f}, u_min={u_fin.min():.4f}")
print(f"v_max={v_fin.max():.4f}, v_min={v_fin.min():.4f}")
print(f"u finite: {np.isfinite(u_fin).all()}, v finite: {np.isfinite(v_fin).all()}")
print(f"mass_u = {np.sum(u_fin)*(L/Nx):.6f}")
print(f"mass_v = {np.sum(v_fin)*(L/Nx):.6f}")
peaks_v, _ = find_peaks(v_fin, height=0.1)
print(f"v peaks at T=8: count={len(peaks_v)}, locs={x[peaks_v].tolist()}")
print(f"TV(u_fin)={np.sum(np.abs(np.diff(u_fin))):.4f}")
print(f"Blow-up: {blow_up_step}")
for i, snap_t in enumerate(snap_times):
    ui, vi = out[i, 0, :], out[i, 1, :]
    pks_v, _ = find_peaks(vi, height=0.1)
    print(f"  t={snap_t:.1f}: u_max={ui.max():.3f}, v_max={vi.max():.3f}, v_peaks={len(pks_v)}")
