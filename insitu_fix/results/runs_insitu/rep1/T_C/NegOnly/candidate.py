"""
E3: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + linear viscosity nu=5e-2 on u.
Per BKdV-S6 deep synthesis: nu_linear=5e-2 controls bore steepening (TV_final~9.6, u_min>=0).

PDE:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx) + nu*u_xx     [nu=0.05 added]
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)

Domain: x in [-15, 15], Nx=256, T=8.0
IC: u = 1.5*(1 - tanh(x/0.5))/2, v = 1.5*sech^2(x+8)
"""
import numpy as np
import os
from scipy.signal import find_peaks

# --- Grid ---
L = 30.0
Nx = 256
x = np.linspace(-L/2, L/2, Nx, endpoint=False)

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# Dealiasing mask (2/3 rule)
dealias_mask = np.zeros(Nx)
n_keep = Nx // 3
dealias_mask[:n_keep] = 1.0
dealias_mask[Nx - n_keep:] = 1.0

def dealias(f):
    fh = np.fft.fft(f)
    fh *= dealias_mask
    return np.real(np.fft.ifft(fh))

# Linear viscosity coefficient for u
nu_u = 5e-2

# --- Initial conditions ---
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0)**2

# --- RHS with 2/3 dealiasing + u-viscosity ---
def rhs(u, v):
    # Dealias state before computing nonlinear products
    u_d = dealias(u)
    v_d = dealias(v)

    uh = np.fft.fft(u_d)
    vh = np.fft.fft(v_d)

    # Linear spectral operators
    u_x = np.real(np.fft.ifft(1j * k * uh))
    v_x = np.real(np.fft.ifft(1j * k * vh))
    v_xx = np.real(np.fft.ifft(-k**2 * vh))
    v_xxx = np.real(np.fft.ifft(-1j * k**3 * vh))
    u_xx = np.real(np.fft.ifft(-k**2 * uh))  # for viscosity

    # Nonlinear products (dealiased)
    uu_x = dealias(u_d * u_x)
    vv_x = dealias(v_d * v_x)
    v2 = dealias(v_d**2)
    uv = dealias(u_d * v_d)

    # d_x(3*v^2 + v_xx)
    coupling_u = np.real(np.fft.ifft(1j * k * np.fft.fft(3.0 * v2 + v_xx)))

    # d_x(u*v)
    coupling_v = np.real(np.fft.ifft(1j * k * np.fft.fft(uv)))

    du_dt = -3.0 * uu_x - coupling_u + nu_u * u_xx   # viscosity on u
    dv_dt = -6.0 * vv_x - v_xxx - coupling_v

    return du_dt, dv_dt

# --- Time stepping ---
T = 8.0
dt = 1e-4
n_steps = int(round(T / dt))

# Snapshot times: 9 snapshots at t=0,1,...,8
snap_every = n_steps // 8

u = u0.copy()
v = v0.copy()

snapshots = []
snapshots.append((0.0, u.copy(), v.copy()))

print(f"Starting E3: Fourier+RK4+2/3-dealias+nu_u={nu_u}, dt={dt}, Nx={Nx}, T={T}")
print(f"Initial: u_max={u.max():.3f}, v_max={v.max():.3f}")

blow_up = False
for step in range(1, n_steps + 1):
    # RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u, v + dt*k3v)

    u = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)

    # Check for blow-up
    if not (np.isfinite(u).all() and np.isfinite(v).all()):
        t_blowup = step * dt
        print(f"BLOW-UP at t={t_blowup:.4f} (step {step})")
        blow_up = True
        break

    # Save snapshots
    if step % snap_every == 0 or step == n_steps:
        t_now = step * dt
        snapshots.append((t_now, u.copy(), v.copy()))
        peaks_v, _ = find_peaks(v, prominence=0.1*max(v.max(), 0.01))
        mass_v = np.sum(v) * L / Nx
        print(f"  t={t_now:.2f}: u_max={u.max():.3f}, u_min={u.min():.3f}, v_max={v.max():.3f}, v_peaks={len(peaks_v)}, mass_v={mass_v:.4f}")

if not blow_up:
    print(f"\nCompleted T={T}")
    print(f"  Final u_max={u.max():.4f}, u_min={u.min():.4f}")
    print(f"  Final v_max={v.max():.4f}")
    peaks_v, _ = find_peaks(v, prominence=0.1*v.max())
    print(f"  Final v peaks: {len(peaks_v)}")

# Build output array: shape (n_snapshots, 2, Nx)
n_out = min(9, len(snapshots))
out = np.zeros((n_out, 2, Nx))
for i, (t, u_snap, v_snap) in enumerate(snapshots[:n_out]):
    out[i, 0, :] = u_snap
    out[i, 1, :] = v_snap

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", out)
print(f"\nSaved pred_results/T_C.npy shape={out.shape}")
print(f"Finite: {np.isfinite(out).all()}")
print(f"u_max across all snapshots: {out[:,0,:].max():.3f}")
print(f"v_max across all snapshots: {out[:,1,:].max():.3f}")
print(f"v_min across all snapshots: {out[:,1,:].min():.3f}")
