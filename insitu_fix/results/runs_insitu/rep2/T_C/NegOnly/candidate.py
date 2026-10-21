"""
E3: Coupled Burgers-swept-KdV solver
Method: Fourier pseudospectral + 2/3-rule dealiasing + classical explicit RK4
       + explicit linear viscosity nu_u=1e-2 on u_xx (reduced from E2's 5e-2)

BKdV-S6 deep synthesis: nu>=1e-2 is the minimum sufficient dissipation for
bore-like ICs (TV_final<=27, u_max_final<=1.62 at T=6). Reducing from 5e-2
to 1e-2 preserves bore control while reducing indirect soliton damping.

PDE:
  u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu_u * u_xx
  v_t = -6*v*v_x - v_xxx - d_x(u*v)

Domain: x in [-15, 15], periodic, Nx=256
T=8.0, dt=2e-4, save 9 snapshots at t=0,1,...,8
nu_u = 1e-2 (explicit in RK4; stable: nu*k_max^2*dt ~ 6e-4 << 2.79)
"""

import numpy as np
import os

# --------------- grid & wavenumbers ---------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Physical wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# 2/3-rule dealiasing mask (keep |k_index| <= Nx//3 = 85)
k_idx = np.fft.fftfreq(Nx, d=1.0 / Nx)
dealias = (np.abs(k_idx) <= Nx // 3).astype(float)

# Viscosity coefficient for u equation (reduced from 5e-2 to 1e-2)
nu_u = 1e-2

# --------------- initial conditions ---------------
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0      # smoothed bore
v = 1.5 / np.cosh(x + 8.0)**2                   # soliton at x=-8

# --------------- RHS function ---------------
def rhs(u, v):
    """RHS of the coupled system with 2/3-rule dealiasing + u-viscosity."""
    # FFT and dealias state
    u_hat = np.fft.fft(u) * dealias
    v_hat = np.fft.fft(v) * dealias

    # Physical-space dealiased variables
    u_d = np.fft.ifft(u_hat).real
    v_d = np.fft.ifft(v_hat).real

    # Spectral derivatives of dealiased fields
    ux = np.fft.ifft(1j * k * u_hat).real
    vx = np.fft.ifft(1j * k * v_hat).real
    vxxx = np.fft.ifft((1j * k)**3 * v_hat).real

    # Viscous diffusion on u: nu_u * u_xx = ifft(-k^2 * u_hat) * nu_u
    u_visc = np.fft.ifft(-k**2 * u_hat).real * nu_u

    # --- u equation RHS: -3*u*u_x - 6*v*v_x - v_xxx + nu_u*u_xx ---
    nl_u_phys = -3.0 * u_d * ux - 6.0 * v_d * vx
    nl_u_hat = np.fft.fft(nl_u_phys) * dealias
    rhs_u = np.fft.ifft(nl_u_hat).real - vxxx + u_visc

    # --- v equation RHS: -6*v*v_x - v_xxx - d_x(u*v) ---
    nl_v_phys = -6.0 * v_d * vx
    nl_v_hat = np.fft.fft(nl_v_phys) * dealias

    uv_hat = np.fft.fft(u_d * v_d) * dealias
    duv = np.fft.ifft(1j * k * uv_hat).real

    rhs_v = np.fft.ifft(nl_v_hat).real - vxxx - duv

    return rhs_u, rhs_v


# --------------- RK4 step ---------------
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)
    return u_new, v_new


# --------------- Time integration ---------------
T = 8.0
dt = 2e-4
n_steps = int(round(T / dt))   # 40000

snap_times = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8], dtype=float)
n_snaps = len(snap_times)
snapshots = np.zeros((n_snaps, 2, Nx))

snap_idx = 0
snap_tol = 0.5 * dt

for step in range(n_steps + 1):
    t = step * dt

    # Save snapshot if due
    if snap_idx < n_snaps and t >= snap_times[snap_idx] - snap_tol:
        snapshots[snap_idx, 0] = u
        snapshots[snap_idx, 1] = v
        snap_idx += 1
        if step % 5000 == 0:
            print(f"  t={t:.2f}  u_max={u.max():.3f}  u_min={u.min():.3f}  v_max={v.max():.3f}")

    if step < n_steps:
        u, v = rk4_step(u, v, dt)

    # Blow-up guard
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"BLOW-UP at t={t:.4f} (step {step})")
        break

# --------------- Save output ---------------
os.makedirs('pred_results', exist_ok=True)
out = snapshots[:snap_idx]
np.save('pred_results/T_C.npy', out)

print(f"\nSaved {snap_idx} snapshots, shape={out.shape}")
print(f"Final t={T}: u_max={u.max():.4f}, u_min={u.min():.4f}, v_max={v.max():.4f}")
print(f"mass_u={u.mean()*L:.6f}, mass_v={v.mean()*L:.6f}")
print(f"u finite: {np.all(np.isfinite(u))}, v finite: {np.all(np.isfinite(v))}")
