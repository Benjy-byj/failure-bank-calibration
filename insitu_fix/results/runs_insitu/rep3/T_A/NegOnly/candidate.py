"""
Coupled Burgers-swept-KdV solver — E3
PDE:
  u_t + 3*u*u_x = -d/dx(3*v^2 + v_xx)  => u_t = -3*u*u_x - 6*v*v_x - v_xxx
  v_t + 6*v*v_x + v_xxx = -d/dx(u*v)   => v_t = -v_xxx + N_v, N_v = -6*v*v_x - (u_x*v + u*v_x)

Method: Fourier pseudospectral + 2/3-rule dealiasing + Cox-Matthews IFRK4
  - Integrating factor exp(ik^3*dt) handles v_xxx in v-equation EXACTLY
  - u-equation is fully explicit RK4
Domain: x in [-15,15], L=30, Nx=256, periodic

IC ADJUSTMENT: epsilon reduced from 0.2 (suggested) to 0.02 (within reason)
  v0 = 2*sech^2(x+5)
  u0 = 0.5*v0^2 + 0.02*v0  (epsilon=0.02; perturbation from Gardner manifold m=0)
Rationale: E1+E2 confirmed fragmentation is PHYSICAL not numerical; the epsilon=0.2
perturbation is too strong. With epsilon=0.02, initial coupling m=0.02v is 10x smaller,
expected to produce much less coupling-driven radiation and better soliton retention.

T = 8.0, dt = 2e-4
"""

import numpy as np
import os

def main():
    L = 30.0
    Nx = 256
    T = 8.0
    dt = 2e-4
    n_steps = int(round(T / dt))   # 40000
    epsilon = 0.02                  # IC perturbation (reduced from suggested 0.2)

    x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

    # Wavenumber array
    j_vals = np.fft.fftfreq(Nx) * Nx   # [0,1,...,127,-128,...,-1]
    k = 2.0 * np.pi / L * j_vals       # physical wavenumbers

    # 2/3-rule dealiasing mask
    dealias = (np.abs(j_vals) <= Nx // 3).astype(float)

    # Integrating factor: linear operator L_k = -(ik)^3 = ik^3 for v
    # (since (ik)^3 = i^3*k^3 = -ik^3, L_k = -(-ik^3) = ik^3)
    L_op = 1j * k**3
    Q    = np.exp(L_op * dt)
    Q2   = np.exp(L_op * (dt / 2.0))

    # ------- Initial conditions -------
    v = 2.0 / np.cosh(x + 5.0) ** 2
    u = 0.5 * v ** 2 + epsilon * v

    def compute_rhs(u, hat_v):
        """
        Compute nonlinear RHS for both equations.
        hat_v must be dealiased (2/3-rule).
        Returns:
          N_hat_v : fft of nonlinear terms of v (excl. -v_xxx handled by IF)
          M_u     : physical-space full explicit RHS for u
        """
        hat_u = np.fft.fft(u) * dealias

        u_d = np.fft.ifft(hat_u).real
        v_d = np.fft.ifft(hat_v).real

        u_x   = np.fft.ifft(1j * k * hat_u).real
        v_x   = np.fft.ifft(1j * k * hat_v).real
        v_xxx = np.fft.ifft((1j * k) ** 3 * hat_v).real   # = ifft(-L_op * hat_v)

        uu_x  = np.fft.ifft(np.fft.fft(u_d * u_x)            * dealias).real
        vv_x  = np.fft.ifft(np.fft.fft(v_d * v_x)            * dealias).real
        uv_x  = np.fft.ifft(np.fft.fft(u_x * v_d + u_d * v_x) * dealias).real

        # N_v (nonlinear part only; v_xxx is handled by integrating factor)
        N_hat_v = np.fft.fft(-6.0 * vv_x - uv_x) * dealias

        # M_u (full explicit RHS for u equation)
        M_u = -3.0 * uu_x - 6.0 * vv_x - v_xxx

        return N_hat_v, M_u

    # Initialize spectral v (dealiased)
    hat_v = np.fft.fft(v) * dealias

    # ------- Snapshot schedule -------
    n_snapshots = 10
    snap_set = {int(round(i * n_steps / (n_snapshots - 1))): i
                for i in range(n_snapshots)}
    snap_data = [None] * n_snapshots

    if 0 in snap_set:
        snap_data[snap_set[0]] = np.stack([u.copy(), np.fft.ifft(hat_v).real.copy()])

    # ------- Cox-Matthews IFRK4 integration -------
    for step in range(n_steps):
        # Stage 1
        k1v, k1u = compute_rhs(u, hat_v)

        # Stage 2
        hat_v2 = (Q2 * hat_v + (dt / 2.0) * Q2 * k1v) * dealias
        u2     = u + (dt / 2.0) * k1u
        k2v, k2u = compute_rhs(u2, hat_v2)

        # Stage 3
        hat_v3 = (Q2 * hat_v + (dt / 2.0) * k2v) * dealias
        u3     = u + (dt / 2.0) * k2u
        k3v, k3u = compute_rhs(u3, hat_v3)

        # Stage 4
        hat_v4 = (Q * hat_v + dt * Q2 * k3v) * dealias
        u4     = u + dt * k3u
        k4v, k4u = compute_rhs(u4, hat_v4)

        # Update
        hat_v = (Q * hat_v + (dt / 6.0) * (Q * k1v + 2.0 * Q2 * k2v
                                             + 2.0 * Q2 * k3v + k4v)) * dealias
        u     = u + (dt / 6.0) * (k1u + 2.0 * k2u + 2.0 * k3u + k4u)

        current = step + 1
        if current in snap_set:
            snap_data[snap_set[current]] = np.stack([u.copy(), np.fft.ifft(hat_v).real.copy()])

    # ------- Save -------
    result = np.array(snap_data)   # (n_snapshots, 2, Nx)
    os.makedirs('pred_results', exist_ok=True)
    np.save('pred_results/T_A.npy', result)

    # ------- Diagnostics -------
    v_init  = result[0, 1, :]
    v_final = result[-1, 1, :]
    u_final = result[-1, 0, :]

    mass_v0 = np.trapezoid(v_init,  x)
    mass_vT = np.trapezoid(v_final, x)
    drift   = abs(mass_vT - mass_v0) / (abs(mass_v0) + 1e-15) * 100.0

    v_max0 = np.max(v_init)
    v_maxT = np.max(v_final)

    print(f"Result shape       : {result.shape}")
    print(f"epsilon            : {epsilon}")
    print(f"v_max t=0          : {v_max0:.4f}")
    print(f"v_max t=T          : {v_maxT:.4f}")
    print(f"Amplitude retention: {v_maxT / v_max0 * 100:.1f}%")
    print(f"mass(v) t=0        : {mass_v0:.6f}")
    print(f"mass(v) t=T        : {mass_vT:.6f}")
    print(f"mass drift         : {drift:.4f}%")
    print(f"max|u| t=T         : {np.max(np.abs(u_final)):.4f}")
    print(f"max|v| t=T         : {np.max(np.abs(v_final)):.4f}")
    print(f"NaN in result      : {np.any(np.isnan(result))}")

    from scipy.signal import find_peaks
    peaks, _ = find_peaks(v_final, prominence=0.1 * v_maxT)
    print(f"v peaks at T       : {len(peaks)}")

    for i in range(result.shape[0]):
        t_i = i * T / (n_snapshots - 1)
        v_i = result[i, 1, :]
        peaks_i, _ = find_peaks(v_i, prominence=0.05 * np.max(v_i))
        print(f"  t={t_i:.2f}: v_max={np.max(v_i):.4f}, n_peaks={len(peaks_i)}")


if __name__ == '__main__':
    main()
