"""
E2: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing
PDE:
  u_t + 3 u u_x = -d/dx(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d/dx(u v)

Domain: x in [-15, 15], periodic, Nx=256
IC: v(x,0) = 4*exp(-(x+5)^2/2.25), u(x,0) = 0
T = 6.0

Change from E1: added 2/3-rule dealiasing to suppress aliasing instability.
"""

import numpy as np
from numpy.fft import fft, ifft, fftfreq
import os

# Parameters
L = 30.0
Nx = 256
T = 6.0
dt = 1e-4
Nt = int(round(T / dt))   # 60000 steps

# Grid
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Wavenumbers
k = 2.0 * np.pi / L * fftfreq(Nx) * Nx

# 2/3-rule dealiasing mask: zero out top 1/3 of modes
# Keep modes |k_index| <= Nx/3
dealias_mask = np.zeros(Nx, dtype=bool)
cutoff = Nx // 3   # = 85
# fftfreq ordering: [0,1,...,N/2-1,-N/2,...,-1] mapped to indices
# Keep indices 0..cutoff and N-cutoff..N-1
dealias_mask[:cutoff + 1] = True
dealias_mask[Nx - cutoff:] = True
dealias_filter = dealias_mask.astype(float)

# Initial conditions
v = 4.0 * np.exp(-(x + 5.0)**2 / 2.25)
u = np.zeros(Nx)

# Precompute spectral operators
ik = 1j * k
ik3 = (1j * k)**3

# Initial mass for drift check
mass_v0 = np.sum(v) * dx

print(f"dt={dt}, Nt={Nt}")
print(f"Dispersive CFL: k_max^3 * dt = {np.max(np.abs(k))**3 * dt:.4f} (< {2*np.sqrt(2):.4f})")
print(f"Dealiasing cutoff wavenumber index: {cutoff} of {Nx//2}")
print(f"Initial v: max={v.max():.4f}, mass={mass_v0:.4f}")


def dealias(U_hat):
    """Apply 2/3-rule dealiasing filter to Fourier coefficients."""
    return U_hat * dealias_filter


def rhs(u, v):
    """Compute RHS using Fourier pseudospectral with 2/3 dealiasing."""
    U = fft(u)
    V = fft(v)

    # Linear derivatives (no dealiasing needed)
    u_x = np.real(ifft(ik * U))
    v_x = np.real(ifft(ik * V))
    v_xxx = np.real(ifft(ik3 * V))

    # Nonlinear products: dealias inputs before forming products
    u_d = np.real(ifft(dealias(U)))
    v_d = np.real(ifft(dealias(V)))
    u_x_d = np.real(ifft(dealias(ik * U)))
    v_x_d = np.real(ifft(dealias(ik * V)))

    # u_t = -3 u u_x - 6 v v_x - v_xxx
    # Apply dealiasing to nonlinear products
    uu_x = dealias(fft(u_d * u_x_d))
    vv_x = dealias(fft(v_d * v_x_d))
    uv_x_product = dealias(fft(u_x_d * v_d + u_d * v_x_d))  # d/dx(u*v) = u_x*v + u*v_x

    f_u = -3.0 * np.real(ifft(uu_x)) - 6.0 * np.real(ifft(vv_x)) - v_xxx
    f_v = -6.0 * np.real(ifft(vv_x)) - v_xxx - np.real(ifft(uv_x_product))

    return f_u, f_v


# Snapshot schedule: 10 snapshots equally spaced
n_snapshots = 10
snap_steps = np.round(np.linspace(Nt / n_snapshots, Nt, n_snapshots)).astype(int)
snap_set = set(snap_steps.tolist())

snapshots = []
nan_detected = False

for step in range(1, Nt + 1):
    # RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)

    u = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)

    if step in snap_set:
        if np.any(np.isnan(u)) or np.any(np.isnan(v)):
            print(f"NaN detected at step {step}, t={step*dt:.4f}")
            nan_detected = True
            # Save what we have
            snapshots.append(np.stack([np.zeros(Nx), np.zeros(Nx)]))
            break
        snapshots.append(np.stack([u.copy(), v.copy()]))
        t_now = step * dt
        mass_now = np.sum(v) * dx
        print(f"  t={t_now:.2f}: v_max={v.max():.4f}, mass_v={mass_now:.4f} (drift={abs(mass_now-mass_v0)/abs(mass_v0)*100:.2f}%)")

# Save results
os.makedirs('pred_results', exist_ok=True)
result = np.array(snapshots)   # shape: (n_snapshots, 2, 256)
np.save('pred_results/T_B.npy', result)

print(f"\nSaved pred_results/T_B.npy: shape={result.shape}")
if not nan_detected:
    print(f"Final v: max={v.max():.4f}, min={v.min():.4f}")
    mass_final = np.sum(v) * dx
    print(f"Mass v: initial={mass_v0:.4f}, final={mass_final:.4f}, drift={abs(mass_final-mass_v0)/abs(mass_v0)*100:.2f}%")

    # Peak counting in final v
    from scipy.signal import find_peaks
    peaks, props = find_peaks(v, height=0.8, distance=5)
    print(f"Peaks in final v with amplitude>=0.8: {len(peaks)} at x={x[peaks]}")
    if len(peaks) > 0:
        print(f"Peak amplitudes: {v[peaks]}")
