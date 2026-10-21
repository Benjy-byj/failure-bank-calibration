"""
E2: Fourier pseudospectral + 2/3-rule dealiasing + explicit classical RK4
     + linear viscosity nu_u=0.05 on u equation only

Coupled Burgers-swept-KdV:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx) + nu_u * u_xx
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)

IC: v0 = 4*exp(-(x+5)^2/2.25), u0 = 0
Domain: x in [-15, 15], periodic, Nx=256, T=6.0

Fix over E1: added nu_u=0.05 viscosity to u equation to prevent Burgers self-flux
from steepening u into a shock (E1 reached TV(u)=654, u_min=-20.8, corrupting v).
BKdV-S6 validates nu_u=5e-2 as sufficient for this regime.
"""
import numpy as np
import os

# ── Parameters ────────────────────────────────────────────────────────────────
L = 30.0
Nx = 256
T = 6.0
dt = 2e-4       # dispersive CFL: dt*k_eff^3 ~1.15 < 2.83 (safe after 2/3 dealias)
nu_u = 0.05     # linear viscosity on u only; nu_u*k_eff^2*dt=0.003 << 2 (stable)
n_snapshots = 10

x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)
k2 = k ** 2

# 2/3-rule dealiasing mask
k_idx = np.arange(Nx)
k_centered = np.where(k_idx <= Nx // 2, k_idx, k_idx - Nx)
dealias_mask = (np.abs(k_centered) <= Nx // 3).astype(float)

# ── Initial condition ──────────────────────────────────────────────────────────
v = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u = np.zeros(Nx)

# ── RHS function ──────────────────────────────────────────────────────────────
def rhs(u, v):
    """Return (u_rhs, v_rhs) for the coupled BKdV system with u-viscosity."""
    # Dealias
    u_hat = np.fft.fft(u) * dealias_mask
    v_hat = np.fft.fft(v) * dealias_mask

    ud = np.fft.ifft(u_hat).real
    vd = np.fft.ifft(v_hat).real

    # Spectral derivatives
    ux = np.fft.ifft(1j * k * u_hat).real
    vx = np.fft.ifft(1j * k * v_hat).real
    vxxx_hat = -1j * k ** 3 * v_hat   # linear dispersive term

    # Nonlinear products (2/3-rule: both inputs dealiased)
    u_ux_hat = np.fft.fft(ud * ux) * dealias_mask
    v2_hat   = np.fft.fft(vd * vd) * dealias_mask
    v_vx_hat = np.fft.fft(vd * vx) * dealias_mask
    uv_hat   = np.fft.fft(ud * vd) * dealias_mask

    # u_t = -3*u*u_x - d_x(3*v^2) - v_xxx + nu_u*u_xx
    # nu_u*u_xx in spectral: -nu_u*k^2*u_hat
    u_rhs_hat = (-3.0 * u_ux_hat
                 - 3j * k * v2_hat
                 - vxxx_hat
                 - nu_u * k2 * u_hat)        # viscous damping (note: -nu*k^2 < 0 → stable)

    # v_t = -6*v*v_x - v_xxx - d_x(u*v)
    v_rhs_hat = -6.0 * v_vx_hat - vxxx_hat - 1j * k * uv_hat

    u_rhs = np.fft.ifft(u_rhs_hat).real
    v_rhs = np.fft.ifft(v_rhs_hat).real
    return u_rhs, v_rhs


# ── Classical RK4 step ────────────────────────────────────────────────────────
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
    return u_new, v_new


# ── Time integration ──────────────────────────────────────────────────────────
n_steps = int(round(T / dt))   # 30000
t_snap = np.linspace(0.0, T, n_snapshots)
step_snap = np.round(t_snap / dt).astype(int)

snapshots = [np.stack([u.copy(), v.copy()])]

snap_idx = 1
for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if snap_idx < n_snapshots and step >= step_snap[snap_idx]:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        snap_idx += 1

result = np.array(snapshots)   # (n_snapshots, 2, Nx)

# ── Save output ───────────────────────────────────────────────────────────────
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", result)

# ── Diagnostics ───────────────────────────────────────────────────────────────
v_final = result[-1, 1]
u_final = result[-1, 0]
dx = L / Nx
print(f"Output shape  : {result.shape}")
print(f"All finite?   : {np.all(np.isfinite(result))}")
print(f"v final: max={v_final.max():.4f}  min={v_final.min():.4f}")
print(f"u final: max={u_final.max():.4f}  min={u_final.min():.4f}")

mass_v0 = np.sum(result[0, 1]) * dx
mass_vT = np.sum(result[-1, 1]) * dx
print(f"mass(v): init={mass_v0:.4f}  final={mass_vT:.4f}  drift={100*abs(mass_vT-mass_v0)/abs(mass_v0):.2f}%")

tv_u = np.sum(np.abs(np.diff(u_final)))
print(f"TV(u) final: {tv_u:.1f}")

try:
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(v_final, height=0.8, distance=8)
    print(f"v peaks >=0.8: count={len(peaks)},  amps={np.round(v_final[peaks], 3)}")
    x_arr = np.linspace(-15, 15, Nx, endpoint=False)
    print(f"  peak x-locations: {np.round(x_arr[peaks], 2)}")
    if len(peaks) > 1:
        seps = np.diff(x_arr[peaks])
        print(f"  peak separations: {np.round(seps, 2)},  min_sep={seps.min():.2f}")
except ImportError:
    print("scipy not available")

print()
print("Snapshot evolution:")
t_snap_vals = np.linspace(0, T, n_snapshots)
for i in range(n_snapshots):
    vi = result[i, 1]
    ui = result[i, 0]
    try:
        from scipy.signal import find_peaks as fp
        pki, _ = fp(vi, height=0.5, distance=5)
        npk = len(pki)
    except Exception:
        npk = -1
    print(f"  t={t_snap_vals[i]:.2f}: v_max={vi.max():.3f}, u_max={ui.max():.3f}, u_min={ui.min():.3f}, n_peaks={npk}")
