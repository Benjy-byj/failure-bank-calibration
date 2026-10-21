"""
FINAL (E2 self-rollback, refined): Fourier pseudospectral + explicit RK4
+ 2/3-rule dealiasing applied ONLY to nonlinear product terms.
Linear dispersive term v_xxx uses full spectrum (exact, no aliasing possible).

Root of E1 failure: aliasing blow-up → fixed by 2/3 rule (E2).
E3 (Hou-Li every step) was over-dissipative → rollback to E2.
Refinement vs original E2: compute v_xxx from full V spectrum (not dealiased)
so the exact dispersive propagation is preserved.

PDE:
  u_t = -3 u u_x - 6 v v_x - v_xxx
  v_t = -6 v v_x - v_xxx - (u v)_x
"""
import numpy as np
from numpy.fft import fft, ifft
import os

# ── Domain ──────────────────────────────────────────────────────────────────
L  = 30.0
Nx = 256
T  = 8.0
dt = 1e-4
n_steps = int(round(T / dt))   # 80000

x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
k = np.fft.fftfreq(Nx, d=1.0/Nx) * (2.0 * np.pi / L)
ik  = 1j * k
ik3 = ik ** 3

# ── 2/3 dealiasing mask (nonlinear terms only) ───────────────────────────────
n_idx   = np.fft.fftfreq(Nx, d=1.0/Nx)
cutoff  = Nx // 3           # 85
dealias = (np.abs(n_idx) <= cutoff).astype(float)

# ── Initial condition ────────────────────────────────────────────────────────
v0 = 2.0 / np.cosh(x + 5.0) ** 2
u0 = 0.5 * v0 ** 2 + 0.2 * v0
state = np.array([u0.copy(), v0.copy()])

# ── RHS ─────────────────────────────────────────────────────────────────────
def rhs(s):
    u, v = s[0], s[1]

    U_full = fft(u)
    V_full = fft(v)

    # Dealiased spectra for nonlinear products only
    U_d = U_full * dealias
    V_d = V_full * dealias

    u_d  = np.real(ifft(U_d))
    v_d  = np.real(ifft(V_d))
    ux_d = np.real(ifft(ik * U_d))
    vx_d = np.real(ifft(ik * V_d))

    # Linear dispersive term: use FULL spectrum (exact, no aliasing for linear)
    vxxx = np.real(ifft(ik3 * V_full))

    # u_t = -3 u u_x - 6 v v_x - v_xxx
    du = -3.0 * u_d * ux_d - 6.0 * v_d * vx_d - vxxx

    # v_t = -6 v v_x - v_xxx - (u v)_x
    dv = -6.0 * v_d * vx_d - vxxx - ux_d * v_d - u_d * vx_d

    return np.array([du, dv])

# ── Snapshots at t = 0, 2, 4, 6, 8 ─────────────────────────────────────────
snap_steps = {0, 20000, 40000, 60000, 80000}
snapshots  = [state.copy()]

# ── RK4 ─────────────────────────────────────────────────────────────────────
for step in range(1, n_steps + 1):
    k1 = rhs(state)
    k2 = rhs(state + 0.5 * dt * k1)
    k3 = rhs(state + 0.5 * dt * k2)
    k4 = rhs(state +       dt * k3)
    state = state + (dt / 6.0) * (k1 + 2.0*k2 + 2.0*k3 + k4)

    if step in snap_steps:
        snapshots.append(state.copy())

    if step % 5000 == 0:
        mv = np.max(np.abs(state[1]))
        mu = np.max(np.abs(state[0]))
        print(f"  step {step:6d}/{n_steps}  max|v|={mv:.4f}  max|u|={mu:.4f}")
        if not np.isfinite(state).all() or mv > 1e6:
            print("DIVERGED"); break

# ── Save ─────────────────────────────────────────────────────────────────────
snapshots = np.array(snapshots)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_A.npy", snapshots)

# ── Diagnostics ──────────────────────────────────────────────────────────────
v0a = snapshots[0, 1]; vfa = snapshots[-1, 1]; ufa = snapshots[-1, 0]
dv  = np.diff(vfa)
n_peaks = int(np.sum((dv[:-1]>0)&(dv[1:]<0)))
amp_ratio = vfa.max() / v0a.max()
mi = v0a.sum()*L/Nx; mf = vfa.sum()*L/Nx
print(f"\nShape        : {snapshots.shape}")
print(f"v_max init   : {v0a.max():.4f}")
print(f"v_max final  : {vfa.max():.4f}")
print(f"u_max final  : {ufa.max():.4f}")
print(f"amp ratio    : {amp_ratio:.4f}  (need >= 0.5)")
print(f"mass drift   : {abs(mf-mi)/abs(mi)*100:.2f}%  (need < 8%)")
print(f"v peak count : {n_peaks}")
print(f"u bounded    : {np.isfinite(ufa).all() and abs(ufa).max()<15}")
print(f"v bounded    : {np.isfinite(vfa).all() and abs(vfa).max()<15}")
