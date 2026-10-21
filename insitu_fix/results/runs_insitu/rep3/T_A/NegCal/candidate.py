"""
E3: Coupled Burgers-swept-KdV soliton stability solver
Method: Same Fourier + 2/3 + RK4 as E1/E2.
IC change from E2: u0 = v0^2/2 (exact Gardner manifold, m=0) instead of m=0.2v.

Motivation: E1 and E2 both gave ~33-34% retention (v_peak=0.66-0.68 at T=8).
The off-manifold source term m_t|_{m=0} = (v-1)(6vv_x+v_xxx) drives fragmentation
(BKdV-S7). With m=0 exactly, this source is minimized, giving the MOST STABLE
scenario for observing soliton survival. BKdV-S4 shows A=1.5, m=0 gives 37%
retention at T=10; A=2.0 at shorter T=8 should show better retention.

We use the same Gardner soliton profile computed in E2 as v0.
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.signal import find_peaks
import os

# ── Domain ──────────────────────────────────────────────────────────────────
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx

# ── Spectral setup ───────────────────────────────────────────────────────────
k = np.fft.fftfreq(Nx, d=dx) * 2.0 * np.pi
ik = 1j * k
ik3 = (1j * k) ** 3

# 2/3-rule dealiasing mask
k_idx = np.abs(np.fft.fftfreq(Nx) * Nx)
mask = (k_idx <= Nx // 3).astype(float)

# ── Gardner soliton (same as E2) ──────────────────────────────────────────────
def compute_gardner_soliton(A, xi_max=25.0, n_pts=10000):
    c = 2.0 * A + A**2 / 4.0

    def ode(xi, y):
        f, fp = y
        fpp = c * f - 3.0 * f**2 - 0.5 * f**3
        return [fp, fpp]

    xi_eval = np.linspace(0.0, xi_max, n_pts)
    sol = solve_ivp(ode, (0.0, xi_max), [A, 0.0], t_eval=xi_eval,
                    method='DOP853', rtol=1e-12, atol=1e-14, max_step=0.01)
    return sol.t, sol.y[0]


A_target = 2.0
xi_pos, f_pos = compute_gardner_soliton(A_target)
print(f"Gardner soliton A={A_target}, c={2*A_target+A_target**2/4}, tail: {f_pos[-1]:.2e}")

# Build soliton on grid centered at x0=-5
x0_soliton = -5.0
v0 = np.zeros(Nx)
for i, xi_val in enumerate(x):
    d = xi_val - x0_soliton
    d = d - L * np.round(d / L)
    d_abs = abs(d)
    if d_abs <= xi_pos[-1]:
        v0[i] = np.interp(d_abs, xi_pos, f_pos)

# u IC: EXACT Gardner manifold (m=0), u0 = v0^2/2
u0 = 0.5 * v0**2
print(f"v0 peak: {np.max(v0):.6f} at x={x[np.argmax(v0)]:.3f}")
print(f"u0 peak: {np.max(u0):.6f}  (m=0 exactly)")
print(f"Mass v0: {np.sum(v0)*dx:.4f}")

# ── RHS (same as E1/E2) ───────────────────────────────────────────────────────
def rhs(u, v):
    u_hat = np.fft.fft(u) * mask
    v_hat = np.fft.fft(v) * mask
    u_d = np.fft.ifft(u_hat).real
    v_d = np.fft.ifft(v_hat).real
    u_x   = np.fft.ifft(ik  * u_hat).real
    v_x   = np.fft.ifft(ik  * v_hat).real
    v_xxx = np.fft.ifft(ik3 * v_hat).real
    uu_x  = u_d * u_x
    vv_x  = v_d * v_x
    uv    = u_d * v_d
    uv_x  = np.fft.ifft(ik * np.fft.fft(uv)).real
    u_rhs = -3.0 * uu_x - 6.0 * vv_x - v_xxx
    v_rhs = -6.0 * vv_x - v_xxx - uv_x
    return u_rhs, v_rhs

# ── RK4 integration ───────────────────────────────────────────────────────────
T_final = 8.0
dt = 2e-4
n_steps = int(round(T_final / dt))

n_snapshots = 10
snap_steps = sorted(set(np.round(np.linspace(0, n_steps, n_snapshots)).astype(int)))

u = u0.copy()
v = v0.copy()
snapshots = []
snap_ptr = 0

print(f"\nRunning {n_steps} steps (E3: Gardner soliton + m=0)...")

for step in range(n_steps + 1):
    if snap_ptr < len(snap_steps) and step == snap_steps[snap_ptr]:
        snapshots.append(np.stack([u.copy(), v.copy()], axis=0))
        snap_ptr += 1
    if step == n_steps:
        break
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,      v + dt*k3v)
    u = u + (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v = v + (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)

# ── Diagnostics ───────────────────────────────────────────────────────────────
result = np.array(snapshots)
print(f"Output shape: {result.shape}")

v_init = result[0, 1]
v_final = result[-1, 1]
u_final = result[-1, 0]

mass_init  = np.sum(v_init)  * dx
mass_final = np.sum(v_final) * dx
mass_drift_pct = abs(mass_final - mass_init) / abs(mass_init) * 100.0

peak_init  = np.max(v_init)
peak_final = np.max(v_final)
u_max_final = np.max(np.abs(u_final))

peaks_idx, _ = find_peaks(v_final, prominence=0.1 * peak_final)
n_peaks = len(peaks_idx)

print(f"\nInitial v peak (Gardner, m=0): {peak_init:.4f}")
print(f"Final   v peak: {peak_final:.4f}  (retention = {peak_final/peak_init:.3f})")
print(f"Mass v drift: {mass_drift_pct:.4f}%")
print(f"Final |u| max: {u_max_final:.4f}")
print(f"Final v dominant peaks (prominence>10%): {n_peaks}")
print(f"All finite: {np.all(np.isfinite(result))}")

T_times = np.linspace(0, T_final, len(result))
print("\nTime series:")
for i, t in enumerate(T_times):
    print(f"  t={t:.2f}: v_peak={np.max(result[i,1]):.4f}, u_max={np.max(np.abs(result[i,0])):.4f}")

print(f"\nPhenomenon check (vs initial 2.0):")
print(f"  v_peak_final >= 1.0: {peak_final >= 1.0} (value={peak_final:.3f})")
print(f"  mass drift < 8%: {mass_drift_pct < 8.0} (value={mass_drift_pct:.4f}%)")
print(f"  |u| < 15: {u_max_final < 15.0} (value={u_max_final:.3f})")
print(f"  |v| < 15: {np.max(np.abs(v_final)) < 15.0}")

# ── Save ──────────────────────────────────────────────────────────────────────
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_A.npy', result)
print("\nSaved pred_results/T_A.npy")
