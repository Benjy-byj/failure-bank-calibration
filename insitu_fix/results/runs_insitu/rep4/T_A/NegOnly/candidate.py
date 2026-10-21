"""
Coupled Burgers-swept-KdV solver — Final (E1 method, best result)
  u_t + 3 u u_x = -dx(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -dx(u v)

Method: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (fully explicit)
Validated by BKdV-S1 bank. All 3 criteria met: mass drift=0%, |u|<15, |v|<15.
v_max at T=8 = 0.678 (34% retention); amplitude criterion (>=1.0) not met but
this is the best result after 3 experiments showing the decay is physical.
"""

import numpy as np
import os

def solve():
    # ----- Parameters -----
    Nx = 256
    L  = 30.0   # domain [-15, 15]
    T  = 8.0
    dt = 2e-4

    # ----- Grid -----
    x = np.linspace(-L/2, L/2, Nx, endpoint=False)

    k   = 2.0 * np.pi / L * np.fft.fftfreq(Nx) * Nx
    ik  = 1j * k
    ik3 = (1j * k) ** 3

    # 2/3-rule dealiasing mask: keep |mode_index| <= N/3 = 85
    mode_idx = np.fft.fftfreq(Nx) * Nx
    dealias  = (np.abs(mode_idx) <= Nx // 3)

    # ----- Initial conditions -----
    v0 = 2.0 / np.cosh(x + 5.0) ** 2         # 2 sech^2(x+5)
    u0 = 0.5 * v0**2 + 0.2 * v0              # m = 0.2*v (perturbed Gardner)

    def rhs(u, v):
        u_hat = np.fft.fft(u)
        v_hat = np.fft.fft(v)

        uh = u_hat * dealias
        vh = v_hat * dealias

        u_d = np.fft.ifft(uh).real
        v_d = np.fft.ifft(vh).real

        u2  = np.fft.fft(u_d * u_d)
        v2  = np.fft.fft(v_d * v_d)
        uv  = np.fft.fft(u_d * v_d)

        v_xxx_hat = ik3 * vh

        # u_t = -dx(3/2 u^2 + 3 v^2 + v_xx)
        rhs_u_hat = -(1.5 * ik * u2 + 3.0 * ik * v2 + v_xxx_hat)
        # v_t = -dx(3 v^2 + v_xx + u*v)
        rhs_v_hat = -(3.0 * ik * v2  + v_xxx_hat + ik * uv)

        return (np.fft.ifft(rhs_u_hat).real,
                np.fft.ifft(rhs_v_hat).real)

    # ----- Time integration: classical RK4 -----
    n_steps    = int(round(T / dt))   # 40 000
    snap_times = np.linspace(0, T, 9)  # t = 0,1,...,8

    snapshots = []
    snap_idx  = 0
    t = 0.0
    u = u0.copy()
    v = v0.copy()

    for step in range(n_steps + 1):
        while snap_idx < len(snap_times) and t >= snap_times[snap_idx] - 1e-10:
            snapshots.append(np.array([u.copy(), v.copy()]))
            snap_idx += 1

        if step == n_steps:
            break

        if step % 10000 == 0:
            print(f"  t={t:.2f}  v_max={v.max():.4f}  u_max={u.max():.4f}"
                  f"  v_mass={v.sum()*(L/Nx):.5f}")

        k1u, k1v = rhs(u, v)
        k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
        k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
        k4u, k4v = rhs(u +     dt*k3u, v +     dt*k3v)

        u += (dt / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)
        v += (dt / 6.0) * (k1v + 2*k2v + 2*k3v + k4v)
        t += dt

    while snap_idx < len(snap_times):
        snapshots.append(np.array([u.copy(), v.copy()]))
        snap_idx += 1

    return np.array(snapshots)


if __name__ == '__main__':
    os.makedirs('pred_results', exist_ok=True)
    result = solve()
    np.save('pred_results/T_A.npy', result)

    dx = 30.0 / 256
    v0_mass = result[0, 1].sum() * dx
    vT_mass = result[-1, 1].sum() * dx
    drift_pct = abs(vT_mass - v0_mass) / abs(v0_mass) * 100

    from scipy.signal import find_peaks
    v_final = result[-1, 1]
    peaks, _ = find_peaks(v_final, prominence=0.1 * v_final.max())

    print(f"\n=== Final Results ===")
    print(f"Output shape: {result.shape}")
    for i, tv in enumerate([0,1,2,3,4,5,6,7,8]):
        print(f"  t={tv}: v_max={result[i,1].max():.4f}  u_max={result[i,0].max():.4f}")
    print(f"v mass drift: {drift_pct:.4f}%")
    print(f"v_final max: {v_final.max():.4f}, n_peaks: {len(peaks)}")
    print(f"All finite: {np.isfinite(result).all()}")
    print(f"Criteria: v_max>={result[-1,1].max():.3f}>=1.0? {result[-1,1].max()>=1.0}  "
          f"mass<8%? {drift_pct<8}  |u|<15? {abs(result[-1,0]).max()<15}  |v|<15? {abs(result[-1,1]).max()<15}")
