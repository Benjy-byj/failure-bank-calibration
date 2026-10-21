"""
E3: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4 + linear viscosity nu=5e-2 on u.
Single change from E2: add nu*u_xx (explicit, spectral) on u-equation.
BKdV-S6 deep synthesis: nu=5e-2 gives u_max_final<=1.62, TV(u)~9.6, u_min>=0 at T=6.

PDE:
  u_t = -3 u u_x - 6 v v_x - v_xxx + nu * u_xx
  v_t = -6 v v_x - v_xxx - u_x v - u v_x
"""
import numpy as np
import os

# Grid
Nx = 256
L = 30.0
x = np.linspace(-L / 2, L / 2, Nx, endpoint=False)

# Wavenumbers for rfft (shape Nx//2+1 = 129)
k_rfft = np.fft.rfftfreq(Nx, d=1.0 / Nx) * (2 * np.pi / L)

# 2/3-rule dealiasing mask: zero modes with k_idx > Nx//3
k_idx = np.arange(Nx // 2 + 1)
dealias_mask = k_idx > Nx // 3  # True for k_idx > 85

# Linear viscosity coefficient on u-equation
nu = 5e-2


def rhs_fn(u, v):
    u_hat = np.fft.rfft(u)
    v_hat = np.fft.rfft(v)

    # Dealiased hat coefficients
    u_hat_d = u_hat.copy()
    u_hat_d[dealias_mask] = 0.0
    v_hat_d = v_hat.copy()
    v_hat_d[dealias_mask] = 0.0

    # Dealiased physical fields
    ud = np.fft.irfft(u_hat_d, n=Nx)
    vd = np.fft.irfft(v_hat_d, n=Nx)

    ik = 1j * k_rfft

    # Derivatives of dealiased fields
    u_x = np.fft.irfft(ik * u_hat_d, n=Nx)
    v_x = np.fft.irfft(ik * v_hat_d, n=Nx)

    # Linear dispersive term (no aliasing issue)
    v_xxx = np.fft.irfft((ik) ** 3 * v_hat, n=Nx)

    # Linear viscosity on u: nu * u_xx (spectral, from full u_hat for accuracy)
    u_xx = np.fft.irfft(-k_rfft ** 2 * u_hat, n=Nx)

    # RHS
    u_t = -3.0 * ud * u_x - 6.0 * vd * v_x - v_xxx + nu * u_xx
    v_t = -6.0 * vd * v_x - v_xxx - u_x * vd - ud * v_x

    return u_t, v_t


def rk4_step(u, v, dt):
    k1u, k1v = rhs_fn(u, v)
    k2u, k2v = rhs_fn(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs_fn(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs_fn(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new


# Initial conditions
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0    # bore: u_L=1.5, u_R=0, center x=0
v0 = 1.5 / np.cosh(x + 8.0) ** 2              # soliton at x=-8

# Stability check: nu * k_max^2 * dt
k_eff = k_rfft[Nx // 3]  # 2/3 dealiasing cutoff wavenumber
print(f"Viscosity CFL: nu*k_eff^2*dt = {nu * k_eff**2 * 1e-4:.4f} (should be << 1)")

# Time stepping
T = 8.0
dt = 1e-4
n_steps = int(round(T / dt))

# Snapshot times: 9 evenly spaced from t=0 to t=T
save_times = np.linspace(0.0, T, 9)
snapshots = []

u, v = u0.copy(), v0.copy()
t = 0.0
save_idx = 0

# Save t=0
snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
save_idx = 1

print(f"Starting E3: Nx={Nx}, dt={dt}, nu={nu}, T={T}, n_steps={n_steps}")
print(f"IC: u_max={u0.max():.4f}, v_max={v0.max():.4f}")

for step in range(n_steps):
    u, v = rk4_step(u, v, dt)
    t += dt

    if save_idx < len(save_times) and t >= save_times[save_idx] - dt * 0.5:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        tv_u = np.sum(np.abs(np.diff(u)))
        print(
            f"  t={t:.3f}: u_max={u.max():.4f}, u_min={u.min():.4f}, "
            f"v_max={v.max():.4f}, TV_u={tv_u:.2f}, "
            f"finite={np.isfinite(u).all() and np.isfinite(v).all()}"
        )
        save_idx += 1

    if not np.isfinite(u).all() or not np.isfinite(v).all():
        print(f"NaN/Inf at t={t:.4f}! Stopping.")
        break

output = np.array(snapshots)
print(f"\nOutput shape: {output.shape}")
print(f"Final u: max={u.max():.4f}, min={u.min():.4f}")
print(f"Final v: max={v.max():.4f}")

# Diagnostics
from scipy.signal import find_peaks
peaks, props = find_peaks(v, prominence=0.05 * max(v.max(), 0.1))
print(f"Final v prominent peaks: {len(peaks)}, v_max={v.max():.4f}")
print(f"TV(u) final: {np.sum(np.abs(np.diff(u))):.4f}")
print(f"mass_u={np.mean(u)*L:.6f} (IC={np.mean(u0)*L:.6f}), mass_v={np.mean(v)*L:.6f} (IC={np.mean(v0)*L:.6f})")

# Phenomenon target checks
print(f"\n--- Phenomenon target checks ---")
print(f"v_max >= 0.5: {v.max():.4f} {'PASS' if v.max() >= 0.5 else 'FAIL'}")
print(f"|u_max| < 5: {max(abs(u.max()), abs(u.min())):.4f} {'PASS' if max(abs(u.max()), abs(u.min())) < 5 else 'FAIL'}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", output)
print(f"\nSaved to pred_results/T_C.npy, shape={output.shape}")
