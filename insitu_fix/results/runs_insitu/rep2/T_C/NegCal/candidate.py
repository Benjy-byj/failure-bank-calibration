#!/usr/bin/env python3
"""
E2: Coupled Burgers-swept-KdV, bore+soliton interaction
PDE:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx)    => u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu*u_xx
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)      => v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x

Method: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (all explicit)
  - Single-component upgrade over E1: add linear u-viscosity nu=5e-2 on u-equation
  - Per BKdV-S6 depth=3: nu>=1e-2 controls bore Gibbs, nu=5e-2 gives TV(u)~9.6, u_min>=0
  - All nonlinear products use dealiased input; v_xxx from dealiased v_hat
  - dt=2e-4 stable: nu*k_eff^2*dt = 5e-2 * 17.8^2 * 2e-4 ~ 3.2e-3 << 1
"""
import numpy as np
import os

def main():
    Nx = 256
    L = 30.0
    T = 8.0
    dt = 2e-4
    n_snap = 8
    nu = 5e-2   # linear u-viscosity (single upgrade over E1)

    x = np.linspace(-L/2, L/2, Nx, endpoint=False)

    # Initial conditions
    u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # smoothed bore: u_L=1.5, u_R=0
    v = 1.5 / np.cosh(x + 8.0)**2                # sech^2 soliton at x=-8, amplitude 1.5

    # Spectral setup
    k_idx = np.fft.fftfreq(Nx, d=1.0/Nx)
    k = 2.0 * np.pi / L * k_idx
    ik = 1j * k
    ik3 = (1j * k)**3
    k2 = k**2   # for u_xx: IFFT(-k2 * u_hat) = u_xx

    # 2/3-rule dealiasing mask
    cutoff = Nx // 3  # 85 for Nx=256
    dealias = (np.abs(k_idx) <= cutoff).astype(float)

    def rhs(u, v):
        u_hat = np.fft.fft(u)
        v_hat = np.fft.fft(v)

        # Dealiased
        u_hat_d = u_hat * dealias
        v_hat_d = v_hat * dealias
        u_d = np.fft.ifft(u_hat_d).real
        v_d = np.fft.ifft(v_hat_d).real

        # Spatial derivatives from dealiased
        u_x = np.fft.ifft(ik * u_hat_d).real
        v_x = np.fft.ifft(ik * v_hat_d).real

        # Dispersive term from dealiased (RK4 stability: k_eff<=85)
        v_xxx = np.fft.ifft(ik3 * v_hat_d).real

        # Linear u-viscosity from dealiased u (explicit, stable since nu*k_eff^2*dt<<1)
        u_xx = np.fft.ifft(-k2 * u_hat_d).real

        # u_t = -3*u*u_x - 6*v*v_x - v_xxx + nu*u_xx
        du = -3.0*u_d*u_x - 6.0*v_d*v_x - v_xxx + nu*u_xx

        # v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x  (no viscosity on v)
        dv = -6.0*v_d*v_x - v_xxx - u_x*v_d - u_d*v_x

        return du, dv

    # Snapshot schedule
    snap_times = np.linspace(0.0, T, n_snap)
    snapshots = np.zeros((n_snap, 2, Nx))
    si = 0

    # t=0 snapshot
    if si < n_snap and snap_times[si] < 1e-12:
        snapshots[si, 0] = u
        snapshots[si, 1] = v
        si += 1

    t = 0.0
    nsteps = round(T / dt)

    for step in range(nsteps):
        k1u, k1v = rhs(u, v)
        k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
        k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
        k4u, k4v = rhs(u + dt*k3u,      v + dt*k3v)

        u = u + (dt/6.0)*(k1u + 2.0*k2u + 2.0*k3u + k4u)
        v = v + (dt/6.0)*(k1v + 2.0*k2v + 2.0*k3v + k4v)
        t += dt

        while si < n_snap and t >= snap_times[si] - 1e-10:
            snapshots[si, 0] = u.copy()
            snapshots[si, 1] = v.copy()
            si += 1

    while si < n_snap:
        snapshots[si, 0] = u
        snapshots[si, 1] = v
        si += 1

    os.makedirs('pred_results', exist_ok=True)
    np.save('pred_results/T_C.npy', snapshots)

    # Diagnostics
    print(f"Shape: {snapshots.shape}")
    print(f"u_max over all snaps: {snapshots[:, 0, :].max():.4f}")
    print(f"u_min over all snaps: {snapshots[:, 0, :].min():.4f}")
    print(f"v_max over all snaps: {snapshots[:, 1, :].max():.4f}")
    print(f"Final u_max: {snapshots[-1, 0, :].max():.4f}")
    print(f"Final u_min: {snapshots[-1, 0, :].min():.4f}")
    print(f"Final v_max: {snapshots[-1, 1, :].max():.4f}")
    dx = L / Nx
    print(f"Mass u: {snapshots[0,0,:].sum()*dx:.4f} -> {snapshots[-1,0,:].sum()*dx:.4f}")
    print(f"Mass v: {snapshots[0,1,:].sum()*dx:.4f} -> {snapshots[-1,1,:].sum()*dx:.4f}")
    print(f"Finite: {np.all(np.isfinite(snapshots))}")
    tv_u = np.sum(np.abs(np.diff(snapshots[-1, 0, :])))
    print(f"TV(u) final: {tv_u:.2f}")

    # Report per-snapshot v peaks
    for i in range(n_snap):
        t_i = snap_times[i]
        vmax_i = snapshots[i, 1, :].max()
        umax_i = snapshots[i, 0, :].max()
        print(f"  t={t_i:.2f}: v_max={vmax_i:.4f}, u_max={umax_i:.4f}")

if __name__ == '__main__':
    main()
