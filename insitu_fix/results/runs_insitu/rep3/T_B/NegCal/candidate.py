"""
E2 (bug-fix rerun): Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing.
Fix from first attempt: all spectral derivatives use dealiased spectrum.
Work in spectral state space to avoid high-mode accumulation in state.
PDE:
  u_t = -3u*u_x - 6v*v_x - v_xxx
       = -(3/2)*d/dx(u^2) - 3*d/dx(v^2) - v_xxx
  v_t = -6v*v_x - v_xxx - d/dx(uv)
       = -3*d/dx(v^2) - v_xxx - d/dx(uv)
Domain: x in [-15,15], periodic, Nx=256
IC: v(x,0) = 4*exp(-(x+5)^2/2.25), u(x,0) = 0
T = 6.0, dt = 2e-4
"""

import numpy as np
import os

# Parameters
L = 30.0
Nx = 256
dx = L / Nx
x = -15.0 + dx * np.arange(Nx)

T = 6.0
dt = 2e-4
n_steps = int(round(T / dt))

# Physical wavenumbers
k = np.fft.fftfreq(Nx, d=dx) * 2 * np.pi

# 2/3-rule dealiasing mask: keep |mode_index| <= Nx/3 = 85
k_idx = np.fft.fftfreq(Nx) * Nx   # integer mode indices: 0,1,...,127,-128,...,-1
dealias_mask = np.abs(k_idx) <= (Nx // 3)  # True for |k_idx| <= 85

def dealias(f_hat):
    """Apply 2/3-rule spectral truncation."""
    return f_hat * dealias_mask


def rhs_spectral(u_hat, v_hat):
    """
    RHS in spectral space. Inputs are dealiased spectral coefficients.
    Returns (u_rhs_hat, v_rhs_hat) in spectral space.

    All spectral derivatives are computed from dealiased spectra.
    Nonlinear products are dealiased after computation.
    """
    # Ensure inputs are dealiased (defensive)
    u_hat_d = dealias(u_hat)
    v_hat_d = dealias(v_hat)

    # Physical-space fields (dealiased)
    u_d = np.real(np.fft.ifft(u_hat_d))
    v_d = np.real(np.fft.ifft(v_hat_d))

    # Nonlinear products in spectral space (dealiased after product)
    u2_hat = dealias(np.fft.fft(u_d * u_d))   # spectrum of u^2, dealiased
    v2_hat = dealias(np.fft.fft(v_d * v_d))   # spectrum of v^2, dealiased
    uv_hat = dealias(np.fft.fft(u_d * v_d))   # spectrum of uv, dealiased

    # Linear dispersive term from dealiased v (critical: use v_hat_d, not v_hat)
    # v_xxx has spectrum (ik)^3 * v_hat = -ik^3 * v_hat
    # -v_xxx has spectrum +ik^3 * v_hat
    neg_vxxx_hat = 1j * k**3 * v_hat_d  # = spectrum of (-v_xxx)

    # RHS in spectral space using flux form for nonlinear terms:
    # u_t = -(3/2)*d/dx(u^2) - 3*d/dx(v^2) - v_xxx
    #      = -(3/2)*ik * u2_hat - 3*ik * v2_hat + neg_vxxx_hat
    u_rhs_hat = -1.5j * k * u2_hat - 3.0j * k * v2_hat + neg_vxxx_hat

    # v_t = -3*d/dx(v^2) - v_xxx - d/dx(uv)
    #      = -3*ik * v2_hat + neg_vxxx_hat - ik * uv_hat
    v_rhs_hat = -3.0j * k * v2_hat + neg_vxxx_hat - 1j * k * uv_hat

    return u_rhs_hat, v_rhs_hat


def rk4_spectral(u_hat, v_hat, dt):
    """RK4 time step in spectral space."""
    k1u, k1v = rhs_spectral(u_hat, v_hat)
    k2u, k2v = rhs_spectral(u_hat + 0.5*dt*k1u, v_hat + 0.5*dt*k1v)
    k3u, k3v = rhs_spectral(u_hat + 0.5*dt*k2u, v_hat + 0.5*dt*k2v)
    k4u, k4v = rhs_spectral(u_hat + dt*k3u, v_hat + dt*k3v)
    u_new = u_hat + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v_hat + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    # Dealias the updated state (keep modes clean)
    return dealias(u_new), dealias(v_new)


# Initial conditions in spectral space
v0 = 4.0 * np.exp(-(x + 5.0)**2 / 2.25)
u0 = np.zeros(Nx)
u_hat = dealias(np.fft.fft(u0))
v_hat = dealias(np.fft.fft(v0))

mass_v0 = np.sum(v0) * dx

# Snapshot setup: 6 snapshots including t=0 and t=T
n_snapshots = 6
snap_times = np.linspace(0, T, n_snapshots)
snap_steps = [int(round(t / dt)) for t in snap_times]
snapshots = np.zeros((n_snapshots, 2, Nx))

# Save t=0
snapshots[0, 0, :] = np.real(np.fft.ifft(u_hat))
snapshots[0, 1, :] = np.real(np.fft.ifft(v_hat))
snap_idx = 1

print(f"E2 (bug-fix): Nx={Nx}, dt={dt}, T={T}, n_steps={n_steps}")
print(f"Snapshot steps: {snap_steps}")
print(f"IC: v_max={v0.max():.4f}, mass_v={mass_v0:.4f}")
print(f"Dealiased modes: {dealias_mask.sum()} / {Nx}")

# Time integration in spectral space
blown_up = False
for step in range(1, n_steps + 1):
    u_hat, v_hat = rk4_spectral(u_hat, v_hat, dt)

    if not np.isfinite(u_hat).all() or not np.isfinite(v_hat).all():
        print(f"BLOW-UP detected at step {step}, t={step*dt:.4f}")
        blown_up = True
        break

    if step in snap_steps and snap_idx < n_snapshots:
        snapshots[snap_idx, 0, :] = np.real(np.fft.ifft(u_hat))
        snapshots[snap_idx, 1, :] = np.real(np.fft.ifft(v_hat))
        snap_idx += 1

    if step % 5000 == 0:
        v_phys = np.real(np.fft.ifft(v_hat))
        u_phys = np.real(np.fft.ifft(u_hat))
        print(f"  step={step}/{n_steps}, t={step*dt:.3f}, v_max={v_phys.max():.4f}, u_max={u_phys.max():.4f}")

if blown_up:
    snapshots[snap_idx:] = np.nan
    print("Run did NOT complete.")
else:
    print(f"Run completed to T={T}.")

# Diagnostics
v_final = snapshots[-1, 1, :]
u_final = snapshots[-1, 0, :]
mass_vf = np.nansum(v_final) * dx
print(f"\n--- Diagnostics ---")
print(f"Final v: max={np.nanmax(v_final):.4f}, min={np.nanmin(v_final):.4f}")
print(f"Final u: max={np.nanmax(u_final):.4f}")
print(f"Mass v: v0={mass_v0:.4f}, vf={mass_vf:.4f}, drift={abs(mass_vf-mass_v0)/abs(mass_v0)*100:.2f}%")

# Peak counting with prominence filter
from scipy.signal import find_peaks
peaks, props = find_peaks(v_final, prominence=0.2*np.nanmax(v_final), distance=Nx//20)
print(f"Final v peaks (prominence>=20% of max): n={len(peaks)}")
if len(peaks) > 0:
    print(f"  amplitudes: {v_final[peaks]}")
    print(f"  x positions: {x[peaks]}")

# Save output
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", snapshots)
print(f"\nSaved pred_results/T_B.npy, shape={snapshots.shape}")
