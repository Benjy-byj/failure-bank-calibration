"""
E3: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4
     + TVD-MUSCL (Rusanov) for u's Burgers advection term
PDE: Coupled Burgers-swept-KdV
  u_t + 3 u u_x = -dx(3v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Single-component upgrade over E2:
  E2 failure mode: u forms a Burgers shock at t~0.5 → spectral blow-up.
  E3 fix: conservative 2nd-order TVD-MUSCL (Rusanov flux) for u's Burgers
  flux -(3u^2/2)_x, capturing the shock as a weak solution without overflow.
  All other terms (v dispersive, v nonlinear, coupling, dealiasing) unchanged.
"""

import numpy as np
import os
import time

# ── Domain ────────────────────────────────────────────────────────────────────
L  = 30.0          # x in [-15, 15]
Nx = 256
x  = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers (rad/m)
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# 2/3-rule dealiasing mask
dealias          = np.ones(Nx)
cutoff           = Nx // 3                    # 85 for Nx=256
dealias[cutoff + 1 : Nx - cutoff] = 0.0      # zero indices 86..170

# ── Time ──────────────────────────────────────────────────────────────────────
T  = 6.0
dt = 1e-4
Nt = int(round(T / dt))
dt = T / Nt

# ── Initial conditions ────────────────────────────────────────────────────────
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# Project IC onto dealiased space
v = np.real(np.fft.ifft(np.fft.fft(v) * dealias))
u = np.real(np.fft.ifft(np.fft.fft(u) * dealias))

# ── TVD-MUSCL Rusanov flux for Burgers term ───────────────────────────────────
def burgers_conservative(u):
    """
    Conservative TVD-MUSCL (minmod + Rusanov) for -(3u^2/2)_x.
    Returns the contribution to u_t from the Burgers nonlinearity.
    """
    f = 1.5 * u ** 2          # Burgers flux F(u) = 3u^2/2

    # MUSCL reconstruction with minmod slope limiter
    du_back = u - np.roll(u,  1)   # u_j - u_{j-1}
    du_fwd  = np.roll(u, -1) - u   # u_{j+1} - u_j

    # Minmod: slope = minmod(du_back, du_fwd)
    sign_b = np.sign(du_back)
    slope  = sign_b * np.maximum(
        0.0, np.minimum(np.abs(du_back), sign_b * du_fwd)
    )

    # Left/right states at interface j+1/2
    u_L = u          + 0.5 * slope                     # left  state at j+1/2
    u_R = np.roll(u, -1) - 0.5 * np.roll(slope, -1)   # right state at j+1/2

    f_L = 1.5 * u_L ** 2
    f_R = 1.5 * u_R ** 2

    # Local Rusanov (LLF) flux at j+1/2
    c_half = 3.0 * np.maximum(np.abs(u_L), np.abs(u_R))  # max |f'| = 3|u|
    F_half = 0.5 * (f_L + f_R) - 0.5 * c_half * (u_R - u_L)

    # Conservative update: -(d/dx) F  via backward difference (periodic)
    return -(F_half - np.roll(F_half, 1)) / dx


# ── RHS ───────────────────────────────────────────────────────────────────────
def rhs(u, v):
    """Returns (du/dt, dv/dt)."""
    u_hat = np.fft.fft(u) * dealias
    v_hat = np.fft.fft(v) * dealias

    ik  = 1j * k
    ik3 = ik ** 3

    # Spectral derivatives for v-related terms
    v_x   = np.real(np.fft.ifft(ik  * v_hat))
    v_xxx = np.real(np.fft.ifft(ik3 * v_hat))

    # Coupling: dx(u*v)
    uv_x  = np.real(np.fft.ifft(ik  * np.fft.fft(u * v) * dealias))

    # u equation:
    #   u_t = -(3u^2/2)_x [TVD-MUSCL]  - 6 v v_x - v_xxx
    du = burgers_conservative(u) - 6.0 * v * v_x - v_xxx

    # v equation (fully spectral):
    #   v_t = -6 v v_x - v_xxx - dx(u v)
    dv = -6.0 * v * v_x - v_xxx - uv_x

    return du, dv


# ── Snapshots ─────────────────────────────────────────────────────────────────
n_snaps    = 10
snap_times = np.linspace(0.0, T, n_snaps)
snaps      = []
snap_idx   = 0

# ── Time-march ────────────────────────────────────────────────────────────────
t0 = time.time()
t  = 0.0

# Save t=0
if snap_idx < n_snaps and t >= snap_times[snap_idx] - 1e-12:
    snaps.append(np.stack([u.copy(), v.copy()]))
    snap_idx += 1

for n in range(Nt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)

    u += (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v += (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)
    t += dt

    while snap_idx < n_snaps and t >= snap_times[snap_idx] - 1e-12:
        snaps.append(np.stack([u.copy(), v.copy()]))
        snap_idx += 1

    # Early abort on blow-up
    if n % 5000 == 0 and n > 0:
        if not np.isfinite(v).all() or not np.isfinite(u).all():
            print(f"Blow-up at t={t:.4f}, step {n}")
            break

wall = time.time() - t0
print(f"Wall time: {wall:.1f}s, steps: {min(n+1, Nt)}, snaps: {len(snaps)}")

# ── Diagnostics ───────────────────────────────────────────────────────────────
result  = np.array(snaps)
v_final = result[-1, 1, :]
u_final = result[-1, 0, :]

print(f"Output shape : {result.shape}")
print(f"v_final  max : {v_final.max():.4f}   min : {v_final.min():.4f}")
print(f"u_final  max : {u_final.max():.4f}   min : {u_final.min():.4f}")
print(f"Finite?      : {np.isfinite(result).all()}")

mass_v0 = np.sum(result[0,  1, :]) * (L / Nx)
mass_vf = np.sum(result[-1, 1, :]) * (L / Nx)
drift   = abs(mass_vf - mass_v0) / (abs(mass_v0) + 1e-12) * 100.0
print(f"Mass v (t=0) : {mass_v0:.4f}")
print(f"Mass v (t=T) : {mass_vf:.4f}")
print(f"Mass drift   : {drift:.2f}%")

# Peak finding in v_final
peaks = []
for i in range(1, Nx - 1):
    if v_final[i] > v_final[i-1] and v_final[i] > v_final[i+1] and v_final[i] >= 0.8:
        peaks.append((x[i], v_final[i]))
print(f"Peaks >=0.8  : {len(peaks)}")
for xp, ap in peaks:
    print(f"   x={xp:.2f}, amp={ap:.4f}")

# Show v profile snapshots
print("\nv_max at each snapshot:")
for s in range(result.shape[0]):
    t_s = snap_times[s] if s < len(snap_times) else T
    print(f"  t={t_s:.3f}: v_max={result[s, 1, :].max():.4f}, u_max={result[s, 0, :].max():.4f}")

# ── Save output ───────────────────────────────────────────────────────────────
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)
print("\nSaved pred_results/T_B.npy")
