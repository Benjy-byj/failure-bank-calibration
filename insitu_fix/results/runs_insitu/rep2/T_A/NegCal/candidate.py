"""
E3: Coupled Burgers-swept-KdV soliton stability solver
Method: Same as E2 (Fourier pseudospectral + 2/3-rule dealiasing + RK4 + full v_hat)
IC change: epsilon = 0.05 instead of 0.2 (4x smaller perturbation from Gardner reduction)
  v(x,0) = 2*sech^2(x+5)
  u(x,0) = 0.5*v^2 + 0.05*v   [was 0.5*v^2 + 0.2*v in E1/E2]

Rationale: E1=E2 give identical converged result (v_max=0.635 at T=8). The large
perturbation 0.2*v drives rapid off-manifold drift. Task allows IC adjustment "within
reason." Reducing epsilon to 0.05 keeps system closer to Gardner reduction and may
allow soliton to retain higher amplitude through T=8.

PDE:
  u_t = -3*u*u_x - 6*v*v_x - v_xxx
  v_t = -6*v*v_x - v_xxx - d_x(u*v)
"""

import numpy as np
import os

# Domain
L = 30.0          # x in [-15, 15]
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Time parameters
T_final = 8.0
dt = 1e-4
n_steps = int(round(T_final / dt))  # 80000 steps

# Fourier wavenumbers (angular)
k = 2.0 * np.pi * np.fft.fftfreq(Nx, d=L/Nx)

# 2/3 dealiasing mask: keep modes |k_idx| <= Nx//3 = 85
k_idx = np.fft.fftfreq(Nx) * Nx   # indices in [-128, 127]
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(float)

# Precomputed quantities
ik = 1j * k
ik3 = 1j * k**3   # -v_xxx_hat = +ik^3*v_hat

k_max = np.abs(k).max()
print(f"RK4 stability: dt * k_max^3 = {dt * k_max**3:.4f} (need < 2.83)")

# Initial conditions — epsilon = 0.05 (smaller perturbation from Gardner)
epsilon = 0.05
v0 = 2.0 / np.cosh(x + 5.0)**2
u0 = 0.5 * v0**2 + epsilon * v0

print(f"IC (epsilon={epsilon}): v_max={v0.max():.4f}, u_max={u0.max():.4f}")
print(f"    mass_v={np.sum(v0)*(L/Nx):.4f}, Gardner deviation m_max={epsilon*v0.max():.4f}")
print(f"Running {n_steps} steps, dt={dt}, T={T_final}")


def rhs(u, v):
    """
    RHS with 2/3-rule dealiasing on nonlinear products only.
    Linear dispersive term uses FULL v_hat (standard pseudospectral).
    """
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Pre-dealiased versions for nonlinear products only
    ud_hat = dealias_mask * u_hat
    vd_hat = dealias_mask * v_hat
    ud = np.real(np.fft.ifft(ud_hat))
    vd = np.real(np.fft.ifft(vd_hat))

    # Spatial derivatives of dealiased fields (for nonlinear terms)
    uxd = np.real(np.fft.ifft(ik * ud_hat))
    vxd = np.real(np.fft.ifft(ik * vd_hat))

    # Dealiased nonlinear products
    uux_hat_d = dealias_mask * np.fft.fft(ud * uxd)   # dealias(u * u_x)
    vvx_hat_d = dealias_mask * np.fft.fft(vd * vxd)   # dealias(v * v_x)
    uv_hat_d  = dealias_mask * np.fft.fft(ud * vd)    # dealias(u * v)

    # u-equation: u_t = -3*u*u_x - 6*v*v_x - v_xxx (uses FULL v_hat for v_xxx)
    rhs_u_hat = -3.0 * uux_hat_d - 6.0 * vvx_hat_d + ik3 * v_hat

    # v-equation: v_t = -6*v*v_x - v_xxx - d_x(u*v) (uses FULL v_hat for v_xxx)
    rhs_v_hat = -6.0 * vvx_hat_d + ik3 * v_hat - ik * uv_hat_d

    rhs_u = np.real(np.fft.ifft(rhs_u_hat))
    rhs_v = np.real(np.fft.ifft(rhs_v_hat))
    return rhs_u, rhs_v


def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    u_new = u + (dt/6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)
    return u_new, v_new


# Snapshot schedule: 10 evenly spaced from step 0 to n_steps
n_snapshots = 10
save_set = set(int(round(i * n_steps / (n_snapshots - 1))) for i in range(n_snapshots))

snapshots = []
u = u0.copy()
v = v0.copy()
mass_v0 = np.sum(v) * (L / Nx)

for step in range(n_steps + 1):
    if step in save_set:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        t_now = step * dt
        mass_v = np.sum(v) * (L / Nx)
        print(f"  t={t_now:.4f}  v_max={v.max():.4f}  u_max={u.max():.4f}  "
              f"mass_v={mass_v:.4f}  finite={np.all(np.isfinite(v)) and np.all(np.isfinite(u))}")
        if not (np.all(np.isfinite(v)) and np.all(np.isfinite(u))):
            print("  *** BLOW-UP DETECTED ***")
            break

    if step < n_steps:
        u, v = rk4_step(u, v, dt)

# Save results
result = np.array(snapshots)   # shape (n_snapshots, 2, Nx)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", result)

# Final diagnostics
v_final = result[-1, 1, :]
u_final = result[-1, 0, :]
mass_v_final = np.sum(v_final) * (L / Nx)
mass_drift_pct = abs(mass_v_final - mass_v0) / abs(mass_v0) * 100.0

print(f"\n=== Final diagnostics ===")
print(f"Output shape: {result.shape}")
print(f"v_final max:  {v_final.max():.6f}  (need >= 1.0)")
print(f"u_final max:  {u_final.max():.6f}  (need < 15)")
print(f"mass_v drift: {mass_drift_pct:.6f}%  (need < 8%)")
print(f"all finite:   {np.all(np.isfinite(result))}")

# Count local maxima in v_final
from scipy.signal import find_peaks
peaks, _ = find_peaks(v_final, prominence=0.1*v_final.max())
print(f"Local peaks in v_final: {len(peaks)}")
print(f"Peak amplitudes: {sorted(v_final[peaks], reverse=True)[:5]}")
print(f"Amplitude retention: {v_final.max()/2.0*100:.1f}% of initial 2.0")
