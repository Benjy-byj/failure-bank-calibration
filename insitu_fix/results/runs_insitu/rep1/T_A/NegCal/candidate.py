"""
E3: Gardner soliton IC + IMEX-CN for v_xxx + explicit midpoint RK2 for u
IC: v0 = exact Gardner soliton (A=2, c=5, peak at x=-5), u0 = 0.5*v0^2 + 0.2*v0
Gardner soliton ODE: (v_x)^2 = v^2*(c - 2v - v^2/4), c=5
  => dv/dxi = -v*sqrt(5 - 2v - v^2/4)  for xi > 0 (right of peak)
PDE:
  u_t = -3*u*u_x - 6*v*v_x - v_xxx
  v_t = -6*v*v_x - v_xxx - d_x(u*v)
"""
import numpy as np
from scipy.integrate import solve_ivp
import os

def compute_gardner_soliton(x_grid, x_peak=-5.0, A=2.0, c=5.0):
    """
    Compute Gardner soliton profile on x_grid.
    ODE: dv/dxi = -v * sqrt(c - 2v - v^2/4)  for xi >= 0 (right side of peak)
    Mirror to get left side.
    """
    # Integrate from xi=0 (v=A) outward to xi_max
    xi_max = 20.0
    n_pts = 10000

    def rhs(xi, v):
        arg = c - 2*v[0] - v[0]**2 / 4.0
        if arg <= 0 or v[0] <= 0:
            return [0.0]
        return [-v[0] * np.sqrt(arg)]

    # Start slightly away from peak to avoid sqrt(0) issue
    eps = 1e-6
    v_start = A - eps  # slightly below peak
    xi_start = 0.0

    sol = solve_ivp(rhs, [xi_start, xi_max], [v_start],
                    method='RK45', max_step=xi_max/n_pts,
                    rtol=1e-10, atol=1e-12)

    xi_arr = sol.t
    v_arr  = sol.y[0]

    # Build symmetric profile: xi < 0 mirrors xi > 0
    # Full xi range: -xi_max to xi_max
    xi_full = np.concatenate([-xi_arr[::-1], xi_arr[1:]])
    v_full  = np.concatenate([ v_arr[::-1],  v_arr[1:]])

    # Interpolate onto x_grid shifted so peak is at x_peak
    xi_on_grid = x_grid - x_peak
    v0 = np.interp(xi_on_grid, xi_full, v_full, left=0.0, right=0.0)
    return v0

def main():
    # Domain
    L  = 30.0
    Nx = 256
    x  = np.linspace(-15.0, 15.0, Nx, endpoint=False)
    dx = L / Nx

    # Wavenumbers
    k = np.fft.fftfreq(Nx, d=dx) * (2 * np.pi)

    # 2/3 dealiasing mask
    k_idx   = np.fft.fftfreq(Nx) * Nx
    dealias = (np.abs(k_idx) <= Nx // 3).astype(float)

    # IMEX-CN coefficients for v_xxx: L_hat = (ik)^3 = -ik^3
    # v_t = -L_hat*v_hat + NL  =>  (1 + 0.5*dt*L_hat)*v^{n+1} = (1 - 0.5*dt*L_hat)*v^n + dt*NL^n
    dt = 5e-4
    L_hat         = (1j * k) ** 3
    cn_denom      = 1.0 + 0.5 * dt * L_hat
    cn_numer_coeff = 1.0 - 0.5 * dt * L_hat

    def nonlinear_v(u, v):
        """Explicit nonlinear RHS for v: -6*v*v_x - d_x(u*v), dealiased."""
        u_hat = np.fft.fft(u); v_hat = np.fft.fft(v)
        u_d   = np.real(np.fft.ifft(u_hat * dealias))
        v_d   = np.real(np.fft.ifft(v_hat * dealias))
        v_x_d = np.real(np.fft.ifft(1j * k * v_hat * dealias))
        vvx_hat = np.fft.fft(6.0 * v_d * v_x_d) * dealias
        uv_hat  = np.fft.fft(u_d * v_d) * dealias
        uv_x    = np.real(np.fft.ifft(1j * k * uv_hat))
        return -np.real(np.fft.ifft(vvx_hat)) - uv_x

    def rhs_u(u, v):
        """Explicit RHS for u: -3*u*u_x - 6*v*v_x - v_xxx, dealiased."""
        u_hat = np.fft.fft(u); v_hat = np.fft.fft(v)
        v_xxx = np.real(np.fft.ifft((1j * k) ** 3 * v_hat))
        u_d   = np.real(np.fft.ifft(u_hat * dealias))
        v_d   = np.real(np.fft.ifft(v_hat * dealias))
        u_x_d = np.real(np.fft.ifft(1j * k * u_hat * dealias))
        v_x_d = np.real(np.fft.ifft(1j * k * v_hat * dealias))
        uu_x_hat = np.fft.fft(3.0 * u_d * u_x_d) * dealias
        vv_x_hat = np.fft.fft(6.0 * v_d * v_x_d) * dealias
        return (-np.real(np.fft.ifft(uu_x_hat))
                - np.real(np.fft.ifft(vv_x_hat))
                - v_xxx)

    # --- Initial conditions: Gardner soliton ---
    v0 = compute_gardner_soliton(x, x_peak=-5.0, A=2.0, c=5.0)
    u0 = 0.5 * v0 ** 2 + 0.2 * v0

    print(f"IC: v_max={v0.max():.4f}, u_max={u0.max():.4f}")
    print(f"IC: mass_v={v0.sum()*dx:.4f}, mass_u={u0.sum()*dx:.4f}")

    T       = 8.0
    n_steps = int(round(T / dt))   # 16000

    snap_times = np.linspace(0, T, 5)
    snap_steps = set(int(round(t / dt)) for t in snap_times)

    u = u0.copy()
    v = v0.copy()
    snapshots = []

    for i in range(n_steps + 1):
        if i in snap_steps:
            snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

        if i == n_steps:
            break

        # --- Step 1: IMEX-CN update for v ---
        v_hat_n  = np.fft.fft(v)
        NL_v     = nonlinear_v(u, v)
        NL_v_hat = np.fft.fft(NL_v) * dealias
        v_hat_new = (cn_numer_coeff * v_hat_n + dt * NL_v_hat) / cn_denom
        v_new = np.real(np.fft.ifft(v_hat_new))

        # --- Step 2: Explicit midpoint RK2 update for u ---
        v_mid  = 0.5 * (v + v_new)
        k1u    = rhs_u(u, v)
        u_half = u + 0.5 * dt * k1u
        k2u    = rhs_u(u_half, v_mid)
        u_new  = u + dt * k2u

        u = u_new
        v = v_new

        if (i + 1) % 4000 == 0:
            t_now = (i + 1) * dt
            print(f"t={t_now:.1f}  v_max={v.max():.4f}  u_max={u.max():.4f}  "
                  f"finite={np.all(np.isfinite(v))}")

    result = np.array(snapshots)
    print(f"\nOutput shape: {result.shape}")
    print(f"All finite: {np.all(np.isfinite(result))}")

    v_final = result[-1, 1, :]
    u_final = result[-1, 0, :]
    print(f"Final v_max={v_final.max():.4f}, v_min={v_final.min():.4f}")
    print(f"Final u_max={u_final.max():.4f}, u_min={u_final.min():.4f}")

    mass_v0 = v0.sum() * dx
    mass_vf = v_final.sum() * dx
    print(f"mass_v: {mass_v0:.4f} -> {mass_vf:.4f}, "
          f"drift={abs(mass_vf-mass_v0)/abs(mass_v0)*100:.2f}%")

    from scipy.signal import find_peaks
    peaks, _ = find_peaks(v_final, prominence=0.1 * max(v_final.max(), 0.01))
    print(f"Peaks in v_final (prominence>=10% vmax): {len(peaks)}")
    if len(peaks) > 0:
        print(f"Peak amplitudes: {v_final[peaks]}")

    os.makedirs('pred_results', exist_ok=True)
    np.save('pred_results/T_A.npy', result)
    print("Saved pred_results/T_A.npy")

if __name__ == '__main__':
    main()
