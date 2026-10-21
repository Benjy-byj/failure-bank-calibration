"""
E3: Coupled Burgers-swept-KdV solver
Method: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + nu=1e-2 linear viscosity on u
Single change from E2: add explicit linear viscosity nu*u_xx to u-RHS to suppress bore Gibbs cascade.
Per BKdV-S6 deep synthesis: nu_lin >= 1e-2 needed for bore-like ICs.

PDE (modified u-equation with viscosity):
  u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu*u_xx
  v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x
"""
import numpy as np
import os
import warnings

warnings.filterwarnings('ignore')

# Domain
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers
k = np.fft.fftfreq(Nx, d=L/Nx) * 2.0 * np.pi

# 2/3 dealiasing mask
k_idx = np.fft.fftfreq(Nx, d=1.0/Nx)
dealias_mask = np.abs(k_idx) <= Nx // 3

# U-side linear viscosity
nu_u = 1e-2

print(f"Setup: Nx={Nx}, L={L}, dt=2e-4, nu_u={nu_u}")
print(f"Dealiasing: keeping {dealias_mask.sum()} of {Nx} modes")

# Stability check
k_eff = (2.0/3.0) * np.pi / (L/Nx)
cfl_visc = nu_u * k_eff**2 * 2e-4
print(f"Viscous CFL: nu*k_eff^2*dt = {cfl_visc:.4f} (should be << 1)")

# Initial conditions
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0     # smoothed bore
v = 1.5 / np.cosh(x + 8.0)**2                  # soliton at x=-8

print(f"IC: u_max={u.max():.3f}, v_max={v.max():.3f}")

def dealias(hat):
    return hat * dealias_mask

def rhs(u, v):
    u_hat = dealias(np.fft.fft(u))
    v_hat = dealias(np.fft.fft(v))

    # Spectral derivatives
    u_x   = np.real(np.fft.ifft(1j * k * u_hat))
    v_x   = np.real(np.fft.ifft(1j * k * v_hat))
    v_xxx = np.real(np.fft.ifft(-1j * k**3 * v_hat))

    # Linear viscosity for u: nu * u_xx = ifft(-nu * k^2 * u_hat)
    u_visc = np.real(np.fft.ifft(-nu_u * k**2 * u_hat))

    # Nonlinear products (dealiased)
    uu_x  = np.real(np.fft.ifft(dealias(np.fft.fft(u * u_x))))
    vv_x  = np.real(np.fft.ifft(dealias(np.fft.fft(v * v_x))))
    ux_v  = np.real(np.fft.ifft(dealias(np.fft.fft(u_x * v))))
    u_vx  = np.real(np.fft.ifft(dealias(np.fft.fft(u * v_x))))

    # u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu*u_xx
    du = -3.0*uu_x - 6.0*vv_x - v_xxx + u_visc

    # v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x
    dv = -6.0*vv_x - v_xxx - ux_v - u_vx

    return du, dv

dt = 2e-4
T  = 8.0
t  = 0.0

n_snapshots = 10
t_save = np.linspace(0.0, T, n_snapshots)
snapshots = []
save_idx = 0

step = 0

while t < T + 1e-10:
    # Save snapshot
    if save_idx < n_snapshots and t >= t_save[save_idx] - 1e-12:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        print(f"  snap t={t:.4f}: u_max={u.max():.3f} u_min={u.min():.3f} "
              f"v_max={v.max():.3f} nan={np.any(np.isnan(u)|np.isnan(v))}")
        save_idx += 1

    if t >= T:
        break

    # Check for blow-up
    if np.any(np.isnan(u) | np.isnan(v)) or np.any(np.isinf(u) | np.isinf(v)):
        print(f"NaN/Inf blow-up at t={t:.4f}, step={step}")
        break

    dt_use = min(dt, T - t)

    # RK4
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt_use*k1u, v + 0.5*dt_use*k1v)
    k3u, k3v = rhs(u + 0.5*dt_use*k2u, v + 0.5*dt_use*k2v)
    k4u, k4v = rhs(u + dt_use*k3u, v + dt_use*k3v)

    u = u + (dt_use/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    v = v + (dt_use/6.0)*(k1v + 2*k2v + 2*k3v + k4v)

    t += dt_use
    step += 1

# Diagnostics
result = np.array(snapshots)
print(f"\nTotal snapshots: {result.shape}")
print(f"Any NaN: {np.any(np.isnan(result))}")

if len(snapshots) >= 1:
    u_final = result[-1, 0]
    v_final = result[-1, 1]

    # Mass conservation
    dx = L / Nx
    mass_u = np.sum(u_final) * dx
    mass_v = np.sum(v_final) * dx
    print(f"Final: u_max={u_final.max():.4f} u_min={u_final.min():.4f}")
    print(f"Final: v_max={v_final.max():.4f} mass_u={mass_u:.4f} mass_v={mass_v:.4f}")

    # TV of u
    tv_u = np.sum(np.abs(np.diff(u_final)))
    print(f"TV(u)_final={tv_u:.2f} (IC TV was ~3.0)")

    # Peak analysis for v
    from scipy.signal import find_peaks
    peaks_v, props = find_peaks(v_final, prominence=0.05*max(v_final.max(), 0.1))
    print(f"v peaks (prominence>5% vmax): {len(peaks_v)}, amplitudes={v_final[peaks_v]}")

    # Check phenomenon targets
    print(f"\nPhenomenon check:")
    print(f"  v_max >= 0.5: {v_final.max() >= 0.5} (v_max={v_final.max():.4f})")
    print(f"  |u_max| < 5:  {abs(u_final.max()) < 5} (|u_max|={abs(u_final.max()):.4f})")
    print(f"  Bore bounded: {abs(u_final.min()) < 5} (u_min={u_final.min():.4f})")

# Save output
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_C.npy', result)
print(f"\nSaved pred_results/T_C.npy shape={result.shape}")
