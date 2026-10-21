"""
E2 (bug-fixed): Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing.
Bug in previous run: dealiasing applied only to products, not to the state itself.
Modes |k_idx|=86..127 in the state were unstable under v_xxx with dt=2e-4
(|dt*k_Nyquist^3| = 3.85 > 3.46 RK4 stability limit for imaginary eigenvalues).
Fix: pre-dealias state at each RHS evaluation (remove modes > 85 from u,v).
BKdV-S1 explicitly says "pre-dealias state at each rhs evaluation".

PDE:
  u_t = -3*u*u_x - 6*v*v_x - v_xxx
  v_t = -(6*v+u)*v_x - v*u_x - v_xxx

Domain: x in [-15, 15], Nx=256, periodic
IC: v(x,0) = 4*exp(-(x+5)^2/2.25),  u(x,0) = 0
T = 6.0,  dt = 2e-4
"""

import numpy as np
import os

# ---- Setup ----
L  = 30.0
Nx = 256
x  = np.linspace(-L/2, L/2, Nx, endpoint=False)
T  = 6.0
dt = 2e-4

# wavenumbers
k = 2.0*np.pi/L * np.fft.fftfreq(Nx, d=1.0/Nx)

# 2/3-rule dealiasing mask: keep |k_idx| <= Nx//3 = 85
c    = Nx // 3   # = 85
mask = np.ones(Nx)
mask[c+1 : Nx-c] = 0.0   # zero indices 86..170

ik  = 1j * k
ik3 = (1j * k)**3

# Initial conditions
v = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u = np.zeros(Nx)
mass0_v = v.sum() * L / Nx

print(f"E2-fixed (2/3 dealias, pre-dealias state): Nx={Nx}, dt={dt}, T={T}")
print(f"IC: v_max={v.max():.4f}, mass_v0={mass0_v:.4f}")
print(f"RK4 CFL with dealiasing: dt*k_eff^3 = {dt*(c*2*np.pi/L)**3:.3f} (< 3.46 needed)")

# ---- RHS with FULL dealiasing (state + products) ----
def rhs(u, v):
    # Pre-dealias state: zero modes |k_idx| > Nx//3
    uh = mask * np.fft.fft(u)
    vh = mask * np.fft.fft(v)

    # Re-project to physical space (dealiased state)
    u  = np.real(np.fft.ifft(uh))
    v  = np.real(np.fft.ifft(vh))

    # All derivatives from dealiased state — max k is c*2pi/L ~ 17.87
    u_x   = np.real(np.fft.ifft(ik  * uh))
    v_x   = np.real(np.fft.ifft(ik  * vh))
    v_xxx = np.real(np.fft.ifft(ik3 * vh))   # stable: dt*k_eff^3 < 3.46

    # Nonlinear products: also dealias (removes aliasing of products)
    def d(arr):
        return np.real(np.fft.ifft(mask * np.fft.fft(arr)))

    uu_x = d(u * u_x)
    vv_x = d(v * v_x)
    uv_x = d(u * v_x)
    vu_x = d(v * u_x)

    u_rhs = -3.0*uu_x - 6.0*vv_x - v_xxx
    v_rhs = -6.0*vv_x - uv_x - vu_x - v_xxx
    return u_rhs, v_rhs

def rk4(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    un = u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    vn = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return un, vn

# ---- Time integration ----
n_snap      = 10
total_steps = int(round(T / dt))
snap_steps  = set(int(round(i*total_steps/(n_snap-1))) for i in range(1, n_snap))

snapshots = np.zeros((n_snap, 2, Nx))
snapshots[0, 0] = u.copy()
snapshots[0, 1] = v.copy()

si      = 1
blow_up = False
t       = 0.0

for step in range(1, total_steps + 1):
    u, v = rk4(u, v, dt)
    t   += dt

    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"BLOW-UP at t={t:.5f}, step={step}")
        blow_up = True
        break

    if step in snap_steps and si < n_snap:
        mass_v = v.sum() * L / Nx
        drift  = (mass_v - mass0_v) / abs(mass0_v) * 100
        from scipy.signal import find_peaks
        pks, _ = find_peaks(v, prominence=0.3, distance=8)
        amps   = sorted([v[p] for p in pks], reverse=True)
        print(f"  t={t:.3f}: v_max={v.max():.4f}, u_max={np.abs(u).max():.4f}, "
              f"mass_drift={drift:.3f}%, n_peaks={len(pks)}, top_amps={amps[:4]}")
        snapshots[si, 0] = u.copy()
        snapshots[si, 1] = v.copy()
        si += 1

if not blow_up and si < n_snap:
    snapshots[si, 0] = u.copy()
    snapshots[si, 1] = v.copy()
    si += 1

os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', snapshots)

# ---- Final diagnostics ----
from scipy.signal import find_peaks
print(f"\nFinal (t={t:.4f}):")
print(f"  shape={snapshots.shape}, all_finite={np.all(np.isfinite(snapshots))}")
print(f"  v_max={v.max():.4f}, v_min={v.min():.4f}, u_max={np.abs(u).max():.4f}")
mass_f = v.sum() * L / Nx
print(f"  mass_v_final={mass_f:.4f}, drift={abs(mass_f-mass0_v)/abs(mass0_v)*100:.3f}%")
pks, _ = find_peaks(v, prominence=0.3, distance=8)
amps   = sorted([v[p] for p in pks], reverse=True)
print(f"  v peaks (prominence>0.3): n={len(pks)}, amplitudes={amps}")
# Check phenomenon target: >=2 peaks with amplitude >=0.8
n_good = sum(1 for a in amps if a >= 0.8)
print(f"  Peaks with amplitude >= 0.8: {n_good} (target: >=2)")
print(f"  PHENOMENON MET: {n_good >= 2 and abs(mass_f-mass0_v)/abs(mass0_v) < 0.08}")
