"""
E3: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing.
Coupled Burgers-swept-KdV:
  u_t + 3 u u_x = -d_x(3 v^2 + v_xx)   =>  u_t = -3 u u_x - 6 v v_x - v_xxx
  v_t + 6 v v_x + v_xxx = -d_x(u v)     =>  v_t = -6 v v_x - v_xxx - (uv)_x
Domain: x in [-15, 15], Nx=256, periodic.
IC: v0 = 2*sech^2(x+5), u0 = 0.2*v0  (adjusted: removes large v0^2/2 term)
    E2 showed u0=v0^2/2+0.2*v0 causes Burgers growth to u_max=6 draining v below threshold.
    This IC uses small initial u (u0_max=0.4) so Burgers dynamics start weak;
    BKdV-S3 shows small-u IC gives 51-63% soliton retention at T=12.
Method: BKdV-S1 deep synthesis working stack (Fourier + 2/3-rule + RK4, dt<=2e-4).
"""
import numpy as np
from numpy.fft import fft, ifft, fftfreq
import os

# ---- Grid ----------------------------------------------------------------
Nx = 256
L = 30.0
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# Wavenumber indices and physical wavenumbers
k_idx = fftfreq(Nx, d=1.0/Nx)        # [0,1,...,127,-128,...,-1]
k = 2.0 * np.pi / L * k_idx

# 2/3-rule dealiasing mask: keep |k_idx| <= Nx//3 = 85
dealias_mask = (np.abs(k_idx) <= Nx // 3).astype(float)

# ---- Initial conditions (E3: small linear u0) ----------------------------
v0 = 2.0 / np.cosh(x + 5.0)**2
u0 = 0.2 * v0      # small linear IC; removes large v0^2/2 term that caused E2 failure

print(f"E3: IC adjustment — u0=0.2*v0 (u0_max={u0.max():.4f} vs E2's {0.5*v0.max()**2+0.2*v0.max():.4f})")

# ---- Time parameters -----------------------------------------------------
T_final = 8.0
dt = 2e-4
n_steps = int(round(T_final / dt))   # 40000 steps

# Snapshot schedule: 9 evenly spaced from t=0 to t=T
n_snapshots = 9
snap_times = np.linspace(0.0, T_final, n_snapshots)
snap_steps = set(int(round(t / dt)) for t in snap_times)
snap_steps.add(0)
snap_steps.add(n_steps)

# ---- Helper: spectral derivative with dealiasing -------------------------
def spec_dx(f_hat):
    return 1j * k * f_hat

def dealias(f_hat):
    return f_hat * dealias_mask

# ---- RHS -----------------------------------------------------------------
def rhs(u, v):
    """
    Compute RHS of coupled BKdV with 2/3-rule dealiasing.
    """
    # Spectral coefficients, dealiased
    u_hat = dealias(fft(u))
    v_hat = dealias(fft(v))

    # Back to physical (dealiased state)
    u_d = ifft(u_hat).real
    v_d = ifft(v_hat).real

    # Spectral derivatives from dealiased hats
    u_x   = ifft(spec_dx(u_hat)).real
    v_x   = ifft(spec_dx(v_hat)).real
    v_xxx = ifft(spec_dx(spec_dx(spec_dx(v_hat)))).real

    # Nonlinear products with dealiasing
    uu_x_hat = dealias(fft(u_d * u_x))
    uu_x = ifft(uu_x_hat).real

    vv_x_hat = dealias(fft(v_d * v_x))
    vv_x = ifft(vv_x_hat).real

    uv_hat = dealias(fft(u_d * v_d))
    uv_x = ifft(spec_dx(uv_hat)).real

    # PDEs
    rhs_u = -3.0 * uu_x - 6.0 * vv_x - v_xxx
    rhs_v = -6.0 * vv_x - v_xxx - uv_x

    return rhs_u, rhs_v


# ---- RK4 step ------------------------------------------------------------
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u +    dt*k3u,  v +    dt*k3v)
    u_new = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new


# ---- Time integration ----------------------------------------------------
u = u0.copy()
v = v0.copy()

snapshots = []
snap_set = sorted(snap_steps)
snap_ptr = 0

# Store t=0
snapshots.append((0.0, u.copy(), v.copy()))
snap_ptr += 1  # 0 already stored

print(f"  dt={dt}, T={T_final}, n_steps={n_steps}")
print(f"  IC: v_max={v0.max():.6f}, u_max={u0.max():.6f}")
print(f"  mass_v_0={np.sum(v0)*dx:.6f}")

blown_up = False

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)

    # Check for blow-up
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        print(f"  BLOW-UP at step {step}, t={step*dt:.4f}")
        blown_up = True
        break

    t = step * dt

    # Scheduled snapshots
    if snap_ptr < len(snap_set) and step == snap_set[snap_ptr]:
        print(f"  t={t:.3f}: v_max={v.max():.4f}, u_max={u.max():.4f}")
        snapshots.append((t, u.copy(), v.copy()))
        snap_ptr += 1

if not blown_up:
    print(f"\nE3 completed successfully!")
    print(f"  v_max_final={v.max():.4f}, u_max_final={u.max():.4f}")
    print(f"  mass_v_final={np.sum(v)*dx:.6f}")
    from scipy.signal import find_peaks
    peaks, props = find_peaks(v, prominence=0.1*v.max(), distance=Nx//20)
    print(f"  n_peaks_v={len(peaks)}")
    if len(peaks) > 0:
        print(f"  dominant_peak_amplitude={v[peaks].max():.4f}")
        print(f"  dominant_peak_x={x[peaks[np.argmax(v[peaks])]]:.4f}")
else:
    print("  E3 FAILED: blow-up")

# ---- Save output ---------------------------------------------------------
os.makedirs("pred_results", exist_ok=True)
n_snaps = len(snapshots)
result = np.zeros((n_snaps, 2, Nx))
for i, (t_i, ui, vi) in enumerate(snapshots):
    result[i, 0, :] = ui
    result[i, 1, :] = vi
np.save("pred_results/T_A.npy", result)
print(f"\nSaved {n_snaps} snapshots to pred_results/T_A.npy, shape={result.shape}")

# ---- Final diagnostics ---------------------------------------------------
if n_snaps >= 2:
    v_final = result[-1, 1, :]
    u_final = result[-1, 0, :]
    mass_v_0 = np.sum(result[0, 1, :]) * dx
    mass_v_f = np.sum(v_final) * dx
    mass_drift_pct = abs(mass_v_f - mass_v_0) / (abs(mass_v_0) + 1e-12) * 100
    print(f"  mass_v: {mass_v_0:.4f} -> {mass_v_f:.4f}, drift={mass_drift_pct:.2f}%")
    print(f"  |max u|={np.abs(u_final).max():.4f}, |max v|={np.abs(v_final).max():.4f}")

    # Phenomenon check
    v_ic_max = result[0, 1, :].max()
    v_final_max = v_final.max()
    threshold = 0.5 * v_ic_max
    print(f"\n  Phenomenon check:")
    print(f"    v_ic_max={v_ic_max:.4f}, threshold={threshold:.4f}")
    print(f"    v_final_max={v_final_max:.4f}")
    print(f"    amplitude_ok={v_final_max >= threshold}")
    print(f"    mass_drift_ok={mass_drift_pct < 8.0}")
    print(f"    bounded_ok={np.abs(u_final).max() < 15 and np.abs(v_final).max() < 15}")
