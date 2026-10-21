"""
Solver for coupled Burgers-swept-KdV system (T_B: Gaussian wave packet -> soliton train).
PDE:
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -∂_x(u v)

Equivalently:
  u_t = -3 u u_x - 6 v v_x - v_xxx
  v_t = -6 v v_x - v_xxx - (u v)_x

Method: Fourier pseudospectral + classical RK4 (fully explicit) + 2/3-rule dealiasing.
Dispersive term applied to DEALIASED v_hat so modes |k_idx|>Nx/3 don't experience
instability (RK4 stability boundary for imaginary eigenvalue: |Omega| <= 2.83).
"""

import numpy as np
import os
import sys

# ── Parameters ────────────────────────────────────────────────────────────────
L = 30.0
Nx = 256
T = 6.0
dt = 2e-4
n_steps = int(round(T / dt))   # 30000

# ── Grid ──────────────────────────────────────────────────────────────────────
x = np.linspace(-L/2, L/2, Nx, endpoint=False)

# ── Wavenumbers ───────────────────────────────────────────────────────────────
k_idx = np.fft.fftfreq(Nx, d=1.0/Nx)
k = (2.0 * np.pi / L) * k_idx

# ── 2/3-rule dealias mask ─────────────────────────────────────────────────────
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(float)
# After dealiasing: k_eff_max = 2*pi*85/30 ≈ 17.8 rad/unit
# Dispersive CFL: dt * k_eff_max^3 ≈ 1.13 < 2.83 (RK4 stable)

# ── Initial conditions ────────────────────────────────────────────────────────
v0 = 4.0 * np.exp(-(x + 5.0)**2 / 2.25)
u0 = np.zeros(Nx)

u_hat = np.fft.fft(u0).astype(complex)
v_hat = np.fft.fft(v0).astype(complex)
u_hat *= dealias_mask
v_hat *= dealias_mask

ik  = 1j * k
ik3 = 1j * k**3   # F[-v_xxx] = -(ik)^3 v̂ = ik^3 v̂

# ── RHS function ─────────────────────────────────────────────────────────────
def rhs(u_hat, v_hat):
    u_hat_d = u_hat * dealias_mask
    v_hat_d = v_hat * dealias_mask

    u   = np.real(np.fft.ifft(u_hat_d))
    v   = np.real(np.fft.ifft(v_hat_d))
    u_x = np.real(np.fft.ifft(ik * u_hat_d))
    v_x = np.real(np.fft.ifft(ik * v_hat_d))

    uu_x_hat = np.fft.fft(u * u_x) * dealias_mask
    vv_x_hat = np.fft.fft(v * v_x) * dealias_mask
    uv_hat   = np.fft.fft(u * v)   * dealias_mask

    # Dispersive term on DEALIASED v_hat (stability requirement)
    disp = ik3 * v_hat_d

    du_hat_dt = -3.0 * uu_x_hat - 6.0 * vv_x_hat + disp
    dv_hat_dt = -6.0 * vv_x_hat + disp - ik * uv_hat

    return du_hat_dt, dv_hat_dt


# ── Snapshot schedule ─────────────────────────────────────────────────────────
n_snaps = 11
snap_step_set = set(int(round(i * n_steps / (n_snaps - 1))) for i in range(n_snaps))
snapshots = []
snap_times = []

def save_snap(t_cur, u_h, v_h):
    u_phys = np.real(np.fft.ifft(u_h))
    v_phys = np.real(np.fft.ifft(v_h))
    snapshots.append(np.stack([u_phys, v_phys], axis=0))
    snap_times.append(t_cur)

if 0 in snap_step_set:
    save_snap(0.0, u_hat, v_hat)
    snap_step_set.discard(0)

# ── RK4 integration ───────────────────────────────────────────────────────────
print(f"RK4: Nx={Nx}, dt={dt:.1e}, n_steps={n_steps}, T={T}")

for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u_hat,              v_hat)
    k2u, k2v = rhs(u_hat + 0.5*dt*k1u, v_hat + 0.5*dt*k1v)
    k3u, k3v = rhs(u_hat + 0.5*dt*k2u, v_hat + 0.5*dt*k2v)
    k4u, k4v = rhs(u_hat + dt*k3u,      v_hat + dt*k3v)

    u_hat += (dt / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_hat += (dt / 6.0) * (k1v + 2*k2v + 2*k3v + k4v)

    # Project back to dealiased subspace after each step
    u_hat *= dealias_mask
    v_hat *= dealias_mask

    if step % 5000 == 0:
        v_c = np.real(np.fft.ifft(v_hat))
        u_c = np.real(np.fft.ifft(u_hat))
        if not np.isfinite(v_c).all():
            print(f"ERROR: NaN at step {step}, t={step*dt:.3f}")
            sys.exit(1)
        print(f"  step {step:6d}/{n_steps}, t={step*dt:.2f}, "
              f"v=[{v_c.min():.3f},{v_c.max():.3f}], u=[{u_c.min():.3f},{u_c.max():.3f}]")

    if step in snap_step_set:
        save_snap(step * dt, u_hat, v_hat)
        snap_step_set.discard(step)

# ── Assemble & save ───────────────────────────────────────────────────────────
result = np.array(snapshots)   # (n_snaps, 2, Nx)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)
print(f"\nSaved pred_results/T_B.npy, shape={result.shape}")

# ── Diagnostics ───────────────────────────────────────────────────────────────
print(f"Snapshot times: {[f'{t:.2f}' for t in snap_times]}")
print(f"All finite: {np.isfinite(result).all()}")

v_final = result[-1, 1, :]
u_final = result[-1, 0, :]
v_init  = result[ 0, 1, :]

print(f"Final v: max={v_final.max():.4f}, min={v_final.min():.4f}")
print(f"Final u: max={u_final.max():.4f}, min={u_final.min():.4f}")

dx = L / Nx
mass_v_0 = np.sum(v_init)  * dx
mass_v_T = np.sum(v_final) * dx
drift_pct = abs(mass_v_T - mass_v_0) / max(abs(mass_v_0), 1e-12) * 100
print(f"mass(v): t=0={mass_v_0:.6f}, T={mass_v_T:.6f}, drift={drift_pct:.4f}%")

from scipy.signal import find_peaks
peaks, _ = find_peaks(v_final, height=0.8, prominence=0.3, distance=Nx//20)
print(f"Peaks (amp>=0.8, prominence>=0.3): count={len(peaks)}")
if len(peaks) > 0:
    for i, p in enumerate(peaks):
        print(f"  peak {i+1}: amp={v_final[p]:.4f}, x={x[p]:.3f}")
