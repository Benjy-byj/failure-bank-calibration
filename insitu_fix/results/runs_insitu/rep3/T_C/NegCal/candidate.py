"""
E3: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + linear viscosity nu_u=5e-2 on u.
Single component change from E2: add u-side linear viscosity nu*u_xx.
BKdV-S6 synthesis recommends nu_u=5e-2 for bore-like ICs: controls bore steepening,
keeps TV(u) low (~9.6 at T=6 vs 235 without viscosity), u_min >= 0.
"""
import numpy as np
import os

def rhs_fn(u, v, k, dealias_mask, nu_u):
    """Compute RHS of coupled Burgers-swept-KdV system.

    PDE:
        u_t + 3 u u_x = -d_x(3 v^2 + v_xx) + nu_u * u_xx
        v_t + 6 v v_x + v_xxx = -d_x(u v)

    Conservation form:
        u_t = -(3/2) d_x(u^2) - 3 d_x(v^2) - v_xxx + nu_u * u_xx
        v_t = -3 d_x(v^2) - v_xxx - d_x(uv)
    """
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Nonlinear products in physical space -> Fourier -> dealias
    u2_hat = np.fft.fft(u**2) * dealias_mask
    v2_hat = np.fft.fft(v**2) * dealias_mask
    uv_hat = np.fft.fft(u * v) * dealias_mask

    # Spectral derivatives of dealiased nonlinear terms
    d_u2 = np.fft.ifft(1j * k * u2_hat).real
    d_v2 = np.fft.ifft(1j * k * v2_hat).real
    d_uv = np.fft.ifft(1j * k * uv_hat).real

    # Linear dispersive term v_xxx (no dealiasing needed for linear term)
    v_xxx = np.fft.ifft((1j * k)**3 * v_hat).real

    # u RHS: -(3/2) d(u^2)/dx - 3 d(v^2)/dx - v_xxx + nu_u * u_xx
    rhs_u = -1.5 * d_u2 - 3.0 * d_v2 - v_xxx
    if nu_u > 0.0:
        rhs_u += nu_u * np.fft.ifft(-k**2 * u_hat).real

    # v RHS: -3 d(v^2)/dx - v_xxx - d(uv)/dx
    rhs_v = -3.0 * d_v2 - v_xxx - d_uv

    return rhs_u, rhs_v


def rk4_step(u, v, dt, k, dealias_mask, nu_u):
    k1u, k1v = rhs_fn(u, v, k, dealias_mask, nu_u)
    k2u, k2v = rhs_fn(u + 0.5*dt*k1u, v + 0.5*dt*k1v, k, dealias_mask, nu_u)
    k3u, k3v = rhs_fn(u + 0.5*dt*k2u, v + 0.5*dt*k2v, k, dealias_mask, nu_u)
    k4u, k4v = rhs_fn(u + dt*k3u, v + dt*k3v, k, dealias_mask, nu_u)
    u_new = u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new


def solve(Nx=256, L=30.0, T=8.0, dt=1e-4, nu_u=0.05):
    # Grid
    x = np.linspace(-L/2, L/2, Nx, endpoint=False)

    # Wavenumbers
    k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

    # 2/3 dealiasing mask
    dealias_mask = np.ones(Nx, dtype=float)
    cutoff = Nx // 3          # 85 for Nx=256
    # Zero high-frequency modes (indices 85..171 for Nx=256)
    dealias_mask[cutoff:Nx-cutoff+1] = 0.0

    # Initial conditions
    u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0       # smoothed bore: u_L=1.5, u_R=0
    v = 1.5 / np.cosh(x + 8.0)**2                    # KdV soliton at x=-8

    print(f"IC: u_max={u.max():.4f}, v_max={v.max():.4f}")
    print(f"CFL check: nu_u*k_max^2*dt = {nu_u*(np.pi*Nx/L)**2*dt:.4f} (<<1 needed)")

    # 9 snapshot times: t=0,1,2,3,4,5,6,7,8
    n_snapshots = 9
    snap_times = np.linspace(0.0, T, n_snapshots)
    snapshots = []
    snap_idx = 0

    t = 0.0
    n_steps = int(round(T / dt))

    # Save t=0 snapshot
    if snap_idx < n_snapshots and t >= snap_times[snap_idx] - 1e-10:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        snap_idx += 1

    for i in range(n_steps):
        u, v = rk4_step(u, v, dt, k, dealias_mask, nu_u)
        t += dt

        # Check for blow-up
        if not np.isfinite(u).all() or not np.isfinite(v).all():
            print(f"BLOWUP at t={t:.4f} step {i+1}")
            snapshots.append(np.stack([u.copy(), v.copy()]))
            break

        # Save snapshot
        if snap_idx < n_snapshots and t >= snap_times[snap_idx] - 1e-10:
            snapshots.append(np.stack([u.copy(), v.copy()]))
            snap_idx += 1
            from scipy.signal import find_peaks
            peaks, _ = find_peaks(v, height=0.1, prominence=0.1)
            print(f"  t={t:.2f}: u_max={u.max():.3f}, u_min={u.min():.3f}, "
                  f"v_max={v.max():.3f}, v_peaks={len(peaks)}, TV(u)={np.sum(np.abs(np.diff(u))):.1f}")

    print(f"\nCompleted t={t:.4f}, saved {len(snapshots)} snapshots")
    print(f"Final u: min={u.min():.4f}, max={u.max():.4f}, finite={np.isfinite(u).all()}")
    print(f"Final v: min={v.min():.4f}, max={v.max():.4f}, finite={np.isfinite(v).all()}")
    print(f"TV(u)={np.sum(np.abs(np.diff(u))):.2f}")

    if np.isfinite(v).all():
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(v, height=0.1, prominence=0.1)
        print(f"v peaks at T: count={len(peaks)}")
        if len(peaks) > 0:
            x_arr = np.linspace(-L/2, L/2, Nx, endpoint=False)
            print(f"  positions: {x_arr[peaks]}")
            print(f"  amplitudes: {v[peaks]}")

    return np.array(snapshots)


if __name__ == "__main__":
    print("=== E3: Fourier pseudospectral + RK4 + 2/3 dealiasing + nu_u=5e-2 ===")
    result = solve(Nx=256, L=30.0, T=8.0, dt=1e-4, nu_u=0.05)
    print(f"Output shape: {result.shape}")

    os.makedirs("pred_results", exist_ok=True)
    np.save("pred_results/T_C.npy", result)
    print("Saved pred_results/T_C.npy")
