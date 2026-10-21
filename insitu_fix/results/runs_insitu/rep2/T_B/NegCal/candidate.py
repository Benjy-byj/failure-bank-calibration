"""
E2: Fourier pseudospectral + 2/3-rule dealiasing + explicit RK4
Same as E1 except dt reduced from 2e-4 to 1e-4 (below k_max^3 stability boundary).

Coupled Burgers-swept-KdV system in conservation form:
  u_t = -d_x( (3/2)*u^2 + 3*v^2 + v_xx )
  v_t = -d_x( 3*v^2 + v_xx + u*v )
Fourier representation:
  u_rhs_hat = 1j*k * [ -(3/2)*u_sq - 3*v_sq + k^2*v ]
  v_rhs_hat = 1j*k * [ -3*v_sq + k^2*v - u*v ]
(u_sq, v_sq, uv are 2/3-rule dealiased; k^2*v is the linear dispersive term, NOT dealiased)

Stability analysis:
  k_max = 128 * 2*pi/30 = 26.81  →  dt_crit = 2.83/k_max^3 = 1.47e-4
  dt=2e-4 gave k_max^3*dt=3.85>2.83 → Nyquist instability (|R|~6.1/step) → blow-up in E1
  dt=1e-4 gives k_max^3*dt=1.93<2.83 → Nyquist mode decays (|R|~0.79/step) → stable
"""
import numpy as np
import os
import sys
from time import time

t0 = time()
print("E2: BKdV soliton-train (Fourier + 2/3-dealias + RK4, dt=1e-4)")
sys.stdout.flush()

# ── Grid ──────────────────────────────────────────────────────────────────────
L   = 30.0
Nx  = 256
x   = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx  = L / Nx
k   = 2*np.pi/L * np.fft.fftfreq(Nx) * Nx   # wavenumbers

# 2/3-rule dealiasing mask  (zero modes |j| > Nx//3 = 85)
k_idx   = np.abs(np.fft.fftfreq(Nx) * Nx)
dealias = (k_idx <= Nx // 3).astype(float)
print(f"  dealias: keep {int(dealias.sum())}/{Nx} modes  (|j|<=85)")

k_max = np.abs(k).max()
k_eff = np.abs(k[dealias.astype(bool)]).max()

# ── Initial condition ──────────────────────────────────────────────────────────
v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u = np.zeros(Nx)

mass_v0 = v.sum() * dx
mass_u0 = u.sum() * dx
print(f"  IC: v_max={v.max():.4f}  mass_v0={mass_v0:.6f}")
print(f"  Stability: k_max^3*dt = {k_max**3 * 1e-4:.4f} < 2.83 (RK4 imag-axis bound)")
sys.stdout.flush()

# ── RHS function ──────────────────────────────────────────────────────────────
def rhs(u, v):
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Dealiased nonlinear products (zero modes |j|>85)
    u_sq_hat = dealias * np.fft.fft(u * u)
    v_sq_hat = dealias * np.fft.fft(v * v)
    uv_hat   = dealias * np.fft.fft(u * v)

    # u_t = 1j*k * [ -(3/2)*u^2 - 3*v^2 + k^2*v ]
    u_rhs_hat = 1j*k * (-(1.5)*u_sq_hat - 3.0*v_sq_hat + k**2*v_hat)
    # v_t = 1j*k * [ -3*v^2 + k^2*v - u*v ]
    v_rhs_hat = 1j*k * (-3.0*v_sq_hat + k**2*v_hat - uv_hat)

    return np.real(np.fft.ifft(u_rhs_hat)), np.real(np.fft.ifft(v_rhs_hat))

# ── Time integration ────────────────────────────────────────────────────────
T_end   = 6.0
dt      = 1e-4                         # <-- reduced from 2e-4 (was unstable)
n_steps = int(round(T_end / dt))       # 60 000
print(f"  n_steps={n_steps}, dt={dt:.2e}")
sys.stdout.flush()

# Snapshot schedule: 10 evenly spaced from 0 to T_end
n_snaps  = 10
snap_set = set(int(round(i * n_steps / (n_snaps - 1))) for i in range(n_snaps))
snap_set.add(n_steps)

snap_data = {}
snap_data[0] = np.stack([u.copy(), v.copy()])

# ── RK4 loop ──────────────────────────────────────────────────────────────────
abort = False
for step in range(1, n_steps + 1):
    k1u, k1v = rhs(u,              v             )
    k2u, k2v = rhs(u+0.5*dt*k1u,  v+0.5*dt*k1v )
    k3u, k3v = rhs(u+0.5*dt*k2u,  v+0.5*dt*k2v )
    k4u, k4v = rhs(u+    dt*k3u,  v+    dt*k3v )

    u += (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v += (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)

    if step in snap_set:
        finite = np.isfinite(u).all() and np.isfinite(v).all()
        snap_data[step] = np.stack([u.copy(), v.copy()])
        print(f"  t={step*dt:.3f}: v_max={v.max():.4f}  u_max={u.max():.4f}  "
              f"mass_v={v.sum()*dx:.6f}  finite={finite}")
        sys.stdout.flush()
        if not finite:
            print("  ABORT: non-finite values")
            abort = True
            break

# ── Assemble output ────────────────────────────────────────────────────────────
sorted_steps = sorted(snap_data.keys())
result = np.array([snap_data[s] for s in sorted_steps])  # (n_snaps, 2, 256)
print(f"\nResult shape: {result.shape}")
print(f"Snapshot times: {[round(s*dt,3) for s in sorted_steps]}")

# ── Diagnostics ───────────────────────────────────────────────────────────────
v_final = result[-1, 1]
u_final = result[-1, 0]

mass_vf = v_final.sum() * dx
drift   = abs(mass_vf - mass_v0) / abs(mass_v0) * 100
print(f"Mass conservation: init={mass_v0:.6f}  final={mass_vf:.6f}  drift={drift:.4f}%")
print(f"v_final: max={v_final.max():.4f}  min={v_final.min():.4f}")
print(f"u_final: max={u_final.max():.4f}  min={u_final.min():.4f}")

# Peak detection (periodic-aware local maxima with amplitude >= 0.8)
arr = v_final
npeaks, peak_amps, peak_xs_idx = 0, [], []
for i in range(Nx):
    il = (i - 1) % Nx
    ir = (i + 1) % Nx
    if arr[i] > arr[il] and arr[i] > arr[ir] and arr[i] >= 0.8:
        # enforce min separation of 10 grid points (periodic)
        if not peak_xs_idx or min((i - peak_xs_idx[-1]) % Nx,
                                  (peak_xs_idx[-1] - i) % Nx) > 10:
            npeaks += 1
            peak_amps.append(float(arr[i]))
            peak_xs_idx.append(i)

print(f"\nPeaks in v_final with amp>=0.8: {npeaks}")
if peak_xs_idx:
    print(f"  amplitudes : {[f'{a:.4f}' for a in peak_amps]}")
    print(f"  x-positions: {[f'{x[j]:.2f}' for j in peak_xs_idx]}")

# ── Save ───────────────────────────────────────────────────────────────────────
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', result)
print(f"\nSaved pred_results/T_B.npy  shape={result.shape}")
print(f"Wall time: {time()-t0:.1f}s")
