"""
E1: Coupled Burgers-swept-KdV solver
Method: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4
PDE:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)
  v_t + 6 v v_x + v_xxx = -d_x(u v)
Domain: x in [-15, 15], periodic, Nx=256
"""
import numpy as np
from numpy.fft import fft, ifft, fftfreq
import os

def solve_bkdv(T=6.0, Nx=256, L=30.0, dt=2e-4, n_snapshots=10):
    # --- Domain ---
    x = np.linspace(-L/2, L/2, Nx, endpoint=False)

    # --- Wavenumbers (standard numpy ordering) ---
    # fftfreq(N, d=1/N) gives [0,1,...,N/2-1,-N/2,...,-1]
    # multiply by 2pi/L to get physical wavenumbers
    k = 2.0 * np.pi / L * fftfreq(Nx, d=1.0/Nx)

    # --- 2/3 dealiasing mask ---
    # Zero all modes with |k_idx| > Nx/3; k_Nyquist = pi*Nx/L
    k_Nyquist = np.pi * Nx / L
    dealias = (np.abs(k) <= (2.0/3.0) * k_Nyquist).astype(float)

    # --- Initial conditions ---
    v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
    u = np.zeros(Nx, dtype=float)

    def compute_rhs(u, v):
        """
        Compute RHS of both equations in physical space.
        All products are dealiased; v_xxx is handled spectrally.
        """
        # Step 1: FFT + dealias the current state
        u_hat = fft(u) * dealias
        v_hat = fft(v) * dealias

        # Step 2: Recover dealiased physical fields
        u_d = ifft(u_hat).real
        v_d = ifft(v_hat).real

        # Step 3: Physical-space first derivatives
        ux = ifft(1j * k * u_hat).real
        vx = ifft(1j * k * v_hat).real

        # Step 4: Dispersive term v_xxx in spectral space
        # (ik)^3 = -ik^3
        vxxx_hat = (-1j * k**3) * v_hat  # dealiased v_hat already applied

        # Step 5: Nonlinear products — compute in physical, FFT, dealias
        # For u equation: -3u*u_x - 6v*v_x - v_xxx
        uu_x_hat = fft(u_d * ux) * dealias       # F{u * u_x}, dealiased
        vv_x_hat = fft(v_d * vx) * dealias       # F{v * v_x}, dealiased

        # For v equation: -6v*v_x - v_xxx - d_x(u*v)
        uv_hat   = fft(u_d * v_d) * dealias      # F{u*v}, dealiased
        uv_x_hat = 1j * k * uv_hat               # F{d_x(uv)}

        # Step 6: Assemble RHS in spectral domain then IFFT
        u_rhs_hat = (-3.0 * uu_x_hat
                     - 6.0 * vv_x_hat
                     - vxxx_hat)

        v_rhs_hat = (-6.0 * vv_x_hat
                     - vxxx_hat
                     - uv_x_hat)

        return ifft(u_rhs_hat).real, ifft(v_rhs_hat).real

    # --- Time stepping setup ---
    n_steps = int(np.round(T / dt))
    # Snapshot schedule: evenly spaced from 0 to T (inclusive)
    t_save = np.linspace(0.0, T, n_snapshots)
    save_steps = set(int(np.round(ts / dt)) for ts in t_save)

    snapshots_t = []
    snapshots_u = []
    snapshots_v = []

    # Save initial state
    if 0 in save_steps:
        snapshots_t.append(0.0)
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())

    report_every = max(1, n_steps // 10)

    for step in range(1, n_steps + 1):
        # Classical RK4
        k1u, k1v = compute_rhs(u, v)
        k2u, k2v = compute_rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
        k3u, k3v = compute_rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
        k4u, k4v = compute_rhs(u + dt*k3u,      v + dt*k3v)

        u = u + (dt/6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
        v = v + (dt/6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)

        if step in save_steps:
            snapshots_t.append(step * dt)
            snapshots_u.append(u.copy())
            snapshots_v.append(v.copy())

        if step % report_every == 0:
            t_now = step * dt
            print(f"  t={t_now:.3f}/{T:.1f}  v_max={v.max():.4f}  u_max={u.max():.4f}"
                  f"  finite={np.isfinite(v).all() and np.isfinite(u).all()}")

    return snapshots_t, snapshots_u, snapshots_v, x

# ============================================================
# Run
# ============================================================
print("Running E1: Fourier+2/3-dealias+RK4, dt=2e-4, T=6.0")
ts, us, vs, x = solve_bkdv(T=6.0, Nx=256, L=30.0, dt=2e-4, n_snapshots=10)

# ============================================================
# Save output
# ============================================================
os.makedirs('pred_results', exist_ok=True)
n_snap = len(ts)
result = np.zeros((n_snap, 2, 256))
for i in range(n_snap):
    result[i, 0] = us[i]
    result[i, 1] = vs[i]

np.save('pred_results/T_B.npy', result)
print(f"\nSaved pred_results/T_B.npy  shape={result.shape}")

# ============================================================
# Diagnostics
# ============================================================
dx = 30.0 / 256
final_v = result[-1, 1]
final_u = result[-1, 0]
init_v  = result[0, 1]

print(f"Snapshot times: {[f'{t:.2f}' for t in ts]}")
print(f"\n--- Final state diagnostics ---")
print(f"finite:   {np.isfinite(result).all()}")
print(f"v max:    {final_v.max():.6f}")
print(f"v min:    {final_v.min():.6f}")
print(f"u max:    {final_u.max():.6f}")
print(f"u min:    {final_u.min():.6f}")

# Mass conservation
mass_v_init  = np.sum(init_v)  * dx
mass_v_final = np.sum(final_v) * dx
drift = abs(mass_v_final - mass_v_init) / (abs(mass_v_init) + 1e-12)
print(f"mass_v: init={mass_v_init:.6f}  final={mass_v_final:.6f}  drift={drift:.4%}")

# Peak detection (criterion for phenomenon target)
try:
    from scipy.signal import find_peaks
    peaks, props = find_peaks(final_v, height=0.8, prominence=0.3, distance=10)
    print(f"\nPeaks in final v (height>=0.8, prominence>=0.3):")
    print(f"  count = {len(peaks)}")
    if len(peaks) > 0:
        print(f"  amplitudes = {final_v[peaks].round(4)}")
        print(f"  x-positions = {x[peaks].round(4)}")
        # Check separation
        if len(peaks) >= 2:
            seps = np.diff(x[peaks])
            print(f"  separations = {seps.round(4)}")
except ImportError:
    # Manual peak detection fallback
    from numpy import gradient
    dv = np.gradient(final_v)
    peaks_manual = np.where((dv[:-1] > 0) & (dv[1:] <= 0) & (final_v[:-1] >= 0.8))[0]
    print(f"Peaks in final v (height>=0.8, manual): count={len(peaks_manual)}")
    if len(peaks_manual) > 0:
        print(f"  amplitudes = {final_v[peaks_manual].round(4)}")
