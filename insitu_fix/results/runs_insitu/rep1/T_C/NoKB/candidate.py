"""
E2: Coupled Burgers-KdV system on periodic domain.
Method: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing
PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)
"""
import numpy as np
import os

# --- Domain ---
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Fourier wavenumbers
k = np.fft.fftfreq(Nx, d=1.0 / Nx) * (2.0 * np.pi / L)

# 2/3-rule dealias mask: zero modes with |n| > Nx/3
n = np.fft.fftfreq(Nx, d=1.0 / Nx)  # integer indices -128..127
dealias_mask = (np.abs(n) <= Nx // 3).astype(float)  # keep |n| <= 85

# --- Initial conditions ---
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0
v0 = 1.5 / np.cosh(x + 8.0) ** 2

print(f"u0 range: [{u0.min():.4f}, {u0.max():.4f}]")
print(f"v0 max:   {v0.max():.4f}  at x={x[np.argmax(v0)]:.2f}")
print(f"Dealias: keeping {int(dealias_mask.sum())} of {Nx} modes")

# --- RHS with dealiasing ---
def rhs(uv):
    u = uv[:Nx]
    v = uv[Nx:]

    u_hat = np.fft.fft(u) * dealias_mask
    v_hat = np.fft.fft(v) * dealias_mask

    # Dealiased physical fields (for nonlinear products)
    u_d = np.fft.ifft(u_hat).real
    v_d = np.fft.ifft(v_hat).real

    # Spectral derivatives of dealiased fields
    ux   = np.fft.ifft(1j * k * u_hat).real
    vx   = np.fft.ifft(1j * k * v_hat).real
    vxx  = np.fft.ifft(-k**2 * v_hat).real
    vxxx = np.fft.ifft(-1j * k**3 * v_hat).real

    # Dealiased nonlinear products: apply mask to their FFT
    three_v2_vxx = 3.0 * v_d**2 + vxx
    three_v2_vxx_hat = np.fft.fft(three_v2_vxx) * dealias_mask
    d_coupling_u = np.fft.ifft(1j * k * three_v2_vxx_hat).real

    uv_prod = u_d * v_d
    uv_hat = np.fft.fft(uv_prod) * dealias_mask
    d_uv = np.fft.ifft(1j * k * uv_hat).real

    u_ux_hat = np.fft.fft(u_d * ux) * dealias_mask
    u_ux = np.fft.ifft(u_ux_hat).real

    v_vx_hat = np.fft.fft(v_d * vx) * dealias_mask
    v_vx = np.fft.ifft(v_vx_hat).real

    du = -3.0 * u_ux - d_coupling_u
    dv = -6.0 * v_vx - vxxx - d_uv

    return np.concatenate([du, dv])

# --- Time integration: explicit RK4 ---
T_final = 8.0
dt = 1e-4
n_steps = int(round(T_final / dt))

# Snapshot times: 10 evenly spaced from 0 to T
n_snap = 10
snap_step_set = set(int(round(i * n_steps / (n_snap - 1))) for i in range(n_snap))
snap_step_set.add(n_steps)

snapshots = []
snap_times_recorded = []

uv = np.concatenate([u0, v0])

for step in range(n_steps + 1):
    if step in snap_step_set:
        u_snap = uv[:Nx].copy()
        v_snap = uv[Nx:].copy()
        snapshots.append(np.stack([u_snap, v_snap]))
        snap_times_recorded.append(step * dt)
        print(f"  snap t={step*dt:.3f}  u_max={u_snap.max():.4f}  v_max={v_snap.max():.4f}"
              f"  any_nan={np.any(np.isnan(uv))}")
        if np.any(np.isnan(uv)) or np.any(np.isinf(uv)):
            print("  *** NaN/Inf detected — stopping early ***")
            break

    if step < n_steps:
        k1 = rhs(uv)
        k2 = rhs(uv + 0.5 * dt * k1)
        k3 = rhs(uv + 0.5 * dt * k2)
        k4 = rhs(uv + dt * k3)
        uv = uv + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

# --- Save ---
snapshots = np.array(snapshots)
print(f"\nFinal output shape: {snapshots.shape}")
if len(snapshots) > 0:
    print(f"Final t={snap_times_recorded[-1]:.3f}  u: [{snapshots[-1,0].min():.4f}, {snapshots[-1,0].max():.4f}]"
          f"  v_max={snapshots[-1,1].max():.4f}")

os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snapshots)
print("Saved pred_results/T_C.npy")
