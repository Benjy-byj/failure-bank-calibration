"""
FINAL candidate — E1 (dt=2e-4), confirmed converged by E3 (dt=5e-5, identical result).

Fourier pseudospectral + 2/3-rule dealiasing (mask applied to ALL terms at rhs entry)
+ explicit RK4. No viscosity (E2 showed viscosity is counterproductive).

Key implementation detail: the 2/3 mask is applied to BOTH u_hat and v_hat at the
BEGINNING of every rhs() call. This prevents high-k modes (|k| > k_cut) from receiving
the k^3 amplification from v_xxx. Without this fix, dt=2e-4 violates the RK4 imaginary-
axis stability bound (dt*k_nyq^3 = 3.85 > 2.83) and blows up at step ~20.

Coupled Burgers-swept-KdV:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx)
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)
"""
import numpy as np
import os

os.makedirs("pred_results", exist_ok=True)

# Grid
Nx = 256
L = 30.0
x = np.linspace(-15, 15, Nx, endpoint=False)

# Wavenumbers
k = 2 * np.pi * np.fft.fftfreq(Nx, d=L / Nx)

# 2/3 dealiasing mask: keeps |k| <= (2/3)*(Nx/2)*(2*pi/L)
k_cut = (2.0 / 3.0) * np.pi * Nx / L
mask = (np.abs(k) <= k_cut).astype(float)


def rhs(u, v):
    # Dealias both fields at entry — all derivatives use only stable modes
    u_hat = np.fft.fft(u) * mask
    v_hat = np.fft.fft(v) * mask

    # Physical fields (dealiased)
    ud = np.fft.ifft(u_hat).real
    vd = np.fft.ifft(v_hat).real

    # First derivatives (dealiased)
    ud_x = np.fft.ifft(1j * k * u_hat).real
    vd_x = np.fft.ifft(1j * k * v_hat).real

    # Third derivative — MUST use dealiased v_hat; otherwise dt*k_nyq^3 > RK4 limit
    v_xxx = np.fft.ifft((1j * k) ** 3 * v_hat).real

    # Quadratic nonlinear products (in dealiased physical space)
    uu_x = ud * ud_x
    vv_x = vd * vd_x
    uv   = ud * vd

    # Spectral derivative of uv — apply mask before derivative
    uv_x = np.fft.ifft(1j * k * np.fft.fft(uv) * mask).real

    # RHS:
    # u_t = -3*u*u_x - 6*v*v_x - v_xxx
    # v_t = -6*v*v_x - v_xxx - (u*v)_x
    rhs_u = -3.0 * uu_x - 6.0 * vv_x - v_xxx
    rhs_v = -6.0 * vv_x - v_xxx - uv_x

    return rhs_u, rhs_v


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5 * dt * k1u, v + 0.5 * dt * k1v)
    k3u, k3v = rhs(u + 0.5 * dt * k2u, v + 0.5 * dt * k2v)
    k4u, k4v = rhs(u + dt * k3u, v + dt * k3v)
    u_new = u + (dt / 6.0) * (k1u + 2 * k2u + 2 * k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2 * k2v + 2 * k3v + k4v)
    return u_new, v_new


# Initial conditions
v0 = 2.0 / np.cosh(x + 5) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0

u = u0.copy()
v = v0.copy()

# Time stepping
T = 8.0
dt = 2e-4
n_steps = int(round(T / dt))  # 40000

# 8 snapshots evenly spaced from t=0 to t=T
n_snaps = 8
snap_step_indices = [int(round(i * n_steps / (n_snaps - 1))) for i in range(n_snaps)]
snap_set = set(snap_step_indices)

snap_u = []
snap_v = []

if 0 in snap_set:
    snap_u.append(u0.copy())
    snap_v.append(v0.copy())

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)

    if np.any(np.isnan(u)) or np.any(np.isnan(v)):
        print(f"NaN detected at step {step}, t={step*dt:.4f}")
        break

    if step in snap_set:
        snap_u.append(u.copy())
        snap_v.append(v.copy())

    if step % 10000 == 0:
        t_now = step * dt
        print(f"t={t_now:.2f}  v_peak={v.max():.4f}  u_max={abs(u).max():.4f}")

# Output array: (n_snapshots, 2, Nx)
out = np.stack([np.array(snap_u), np.array(snap_v)], axis=1)
np.save("pred_results/T_A.npy", out)
print(f"Saved shape: {out.shape}")

# Diagnostics
v_final = snap_v[-1]
u_final = snap_u[-1]
v0_mass = np.sum(v0) * L / Nx
vf_mass = np.sum(v_final) * L / Nx
print(f"v0 peak: {v0.max():.4f}")
print(f"v_final peak: {v_final.max():.4f}  (criterion: >= 1.0)")
print(f"mass(v) initial: {v0_mass:.4f}  final: {vf_mass:.4f}")
print(f"mass drift: {abs(vf_mass - v0_mass) / abs(v0_mass) * 100:.2f}%  (criterion: < 8%)")
print(f"u_final |max|: {abs(u_final).max():.4f}  (criterion: < 15)")
print(f"v_final |max|: {abs(v_final).max():.4f}  (criterion: < 15)")
print(f"NaN check: u={np.any(np.isnan(u_final))}, v={np.any(np.isnan(v_final))}")
