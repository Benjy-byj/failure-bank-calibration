#!/usr/bin/env python3
"""
Experiment E3: Coupled Burgers-swept-KdV solver.
Method: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4
        + targeted linear viscosity eps_u * u_xx on u equation only

Change from E2: reduced eps_u from 0.05 to 0.005 (10x smaller).
Rationale: E2 (eps_u=0.05) over-damped u, reducing u_max from 6.03 to 0.948
and WORSENING v_peak from 0.635 to 0.405. Root cause: eps_u=0.05 damps
soliton-scale (low-k) u modes, destroying u-v phase coherence.
eps_u=0.005 selectively damps only high-k Burgers shock modes:
  k=1: e^{-eps*k^2*T} = e^{-0.04} = 0.96 (4% decay -- negligible)
  k=15: e^{-0.9} = 0.41 (59% decay -- suppresses shock edge pile-up)
This targets the Burgers high-k cascade while preserving u-v coherence.

PDE:
  u_t = -d_x(3u^2/2 + 3v^2) - v_xxx + eps_u * u_xx
  v_t = -d_x(3v^2 + u*v) - v_xxx

Domain: x in [-15, 15], periodic, Nx=256
IC: v0 = 2*sech^2(x+5),  u0 = 0.5*v0^2 + 0.2*v0
T = 8.0, dt = 2e-4, eps_u = 0.005
"""

import numpy as np
import os
import sys

# ============================================================
# Parameters
# ============================================================
Nx = 256
L = 30.0          # domain [-L/2, L/2] = [-15, 15]
T = 8.0
dt = 2.0e-4       # confirmed safe by BKdV-S1 with 2/3 dealiasing
eps_u = 0.005     # targeted linear viscosity on u (10x smaller than E2)
n_snapshots = 10  # at least 5 required

# ============================================================
# Grid
# ============================================================
x = np.linspace(-L/2, L/2, Nx, endpoint=False)

# ============================================================
# Initial Conditions
# ============================================================
v0 = 2.0 / np.cosh(x + 5.0)**2
u0 = 0.5 * v0**2 + 0.2 * v0

# ============================================================
# Spectral Setup
# ============================================================
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# 2/3-rule dealiasing mask: keep modes with |mode_index| <= Nx//3
mode_idx = np.fft.fftfreq(Nx, d=1.0/Nx).astype(int)
dealias = (np.abs(mode_idx) <= Nx // 3).astype(float)
# Nx//3 = 85 for Nx=256: keeps 171/256 ~ 2/3 of modes

# Precompute spectral operators
k2 = k**2  # for u_xx: (ik)^2 = -k^2, so u_xx -> -k^2 * u_hat

# ============================================================
# RHS Function
# ============================================================
def rhs(u, v):
    """
    Compute RHS of coupled system.
    u gets eps_u * u_xx (targeted linear viscosity, treated explicitly in RK4).
    Uses divergence form for exact mass conservation.
    Applies 2/3-rule dealiasing to all nonlinear products.
    """
    # Dealiase inputs
    u_hat = np.fft.fft(u) * dealias
    v_hat = np.fft.fft(v) * dealias

    # Physical-space dealiased fields
    u_d = np.fft.ifft(u_hat).real
    v_d = np.fft.ifft(v_hat).real

    # Nonlinear fluxes (divergence form)
    F_u = 1.5 * u_d**2 + 3.0 * v_d**2   # flux for u: 3u^2/2 + 3v^2
    F_v = 3.0 * v_d**2 + u_d * v_d        # flux for v: 3v^2 + uv

    # Spectral transforms of fluxes (dealias products)
    F_u_hat = np.fft.fft(F_u) * dealias
    F_v_hat = np.fft.fft(F_v) * dealias

    # Dispersive term: -v_xxx in spectral = -(ik)^3 * v_hat
    disp_hat = -(1j * k)**3 * v_hat

    # Targeted linear viscosity on u: +eps_u * u_xx = -eps_u * k^2 * u_hat
    # Selectively damps high-k Burgers shock modes while preserving low-k soliton
    visc_u_hat = -eps_u * k2 * u_hat

    # Full RHS in spectral space
    rhs_u = np.fft.ifft(-1j * k * F_u_hat + disp_hat + visc_u_hat).real
    rhs_v = np.fft.ifft(-1j * k * F_v_hat + disp_hat).real

    return rhs_u, rhs_v

# ============================================================
# Classical RK4 Step
# ============================================================
def rk4_step(u, v):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + dt * (k1u + 2.0*k2u + 2.0*k3u + k4u) / 6.0
    v_new = v + dt * (k1v + 2.0*k2v + 2.0*k3v + k4v) / 6.0
    return u_new, v_new

# ============================================================
# Time Integration
# ============================================================
n_steps = int(np.round(T / dt))  # 40000 steps

# Snapshot indices: n_snapshots evenly spaced from step 0 to step n_steps
snap_indices = np.round(np.linspace(0, n_steps, n_snapshots)).astype(int)
snap_indices[-1] = n_steps  # ensure final step is included
snap_set = set(snap_indices.tolist())

u = u0.copy()
v = v0.copy()
snapshots = []
snap_times = []

mass_v0 = np.sum(v0) * L / Nx  # initial mass of v

print(f"n_steps={n_steps}, dt={dt}, T={T}, eps_u={eps_u}")
print(f"Snapshot at steps: {snap_indices.tolist()}")
print(f"Initial: v_max={np.max(v0):.4f}, u_max={np.max(u0):.4f}, mass_v={mass_v0:.4f}")

for step in range(n_steps + 1):
    if step in snap_set:
        t = step * dt
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_times.append(t)

        # Diagnostics
        v_max = np.max(v)
        u_max_abs = np.max(np.abs(u))
        mass_v = np.sum(v) * L / Nx
        mass_drift_pct = abs(mass_v - mass_v0) / abs(mass_v0) * 100.0
        is_finite = np.isfinite(u).all() and np.isfinite(v).all()

        print(f"t={t:.3f}: v_peak={v_max:.4f}, |u|_max={u_max_abs:.4f}, "
              f"mass_v={mass_v:.4f} (drift={mass_drift_pct:.2f}%), finite={is_finite}")

        if not is_finite:
            print("ERROR: NaN/Inf detected! Stopping early.")
            sys.exit(1)

    if step < n_steps:
        u, v = rk4_step(u, v)

# ============================================================
# Save Output
# ============================================================
output = np.stack(snapshots, axis=0)  # shape (n_snapshots, 2, 256)
print(f"\nOutput shape: {output.shape}")
print(f"Times saved: {snap_times}")

os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_A.npy', output)
print("Saved to pred_results/T_A.npy")

# Final diagnostics
v_final = output[-1, 1, :]
u_final = output[-1, 0, :]
v0_arr = output[0, 1, :]
print(f"\n=== Final Diagnostics ===")
print(f"v_max(T=8): {np.max(v_final):.4f}  (initial: {np.max(v0_arr):.4f})")
print(f"v_max / v_max0: {np.max(v_final)/np.max(v0_arr):.4f}")
print(f"|u|_max(T=8): {np.max(np.abs(u_final)):.4f}")
mass_v_final = np.sum(v_final) * L / Nx
mass_v_init = np.sum(v0_arr) * L / Nx
print(f"mass_v(T=8): {mass_v_final:.4f}, mass_v(0): {mass_v_init:.4f}")
print(f"mass drift: {abs(mass_v_final-mass_v_init)/abs(mass_v_init)*100:.2f}%")
# Count local maxima in v_final
dv = np.diff(v_final)
n_peaks = np.sum((dv[:-1] > 0) & (dv[1:] < 0))
print(f"Local maxima count in v(T=8): {n_peaks}")
print(f"Phenomenon check: v_peak >= 1.0? {np.max(v_final) >= 1.0}")
print(f"Phenomenon check: mass drift < 8%? {abs(mass_v_final-mass_v_init)/abs(mass_v_init)*100 < 8.0}")
print(f"Phenomenon check: |max| < 15? u={np.max(np.abs(u_final))<15}, v={np.max(np.abs(v_final))<15}")
