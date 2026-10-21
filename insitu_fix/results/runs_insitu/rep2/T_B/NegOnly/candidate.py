"""
E3: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing + linear viscosity on u.
Coupled Burgers-swept-KdV system.
Single upgrade from E2: add nu_u * u_xx to u equation to damp Burgers shock cascade.
nu_u = 1e-2 (per BKdV-S6 deep synthesis for bore-like u gradients).
CFL for nu_u: nu_u * k_max_dealias^2 * dt = 1e-2 * 319 * 1e-4 = 3.2e-4 << 1 (stable).
"""
import numpy as np
import os
from scipy.signal import find_peaks

# ── Grid ──────────────────────────────────────────────────────────────────────
Nx   = 256
L    = 30.0        # domain [-15, 15]
x    = np.linspace(-L/2, L/2, Nx, endpoint=False)
k    = (2.0 * np.pi / L) * np.fft.fftfreq(Nx, d=1.0/Nx)

# ── Parameters ────────────────────────────────────────────────────────────────
T        = 6.0
dt       = 1e-4
n_steps  = int(round(T / dt))
dt       = T / n_steps

# Linear viscosity on u (damps Burgers shock in u)
nu_u = 1e-2

# 2/3 dealiasing mask: keep modes |k_idx| <= Nx//3 = 85
cutoff  = Nx // 3   # = 85
mask    = np.ones(Nx, dtype=bool)
mask[cutoff+1 : Nx-cutoff] = False   # zero out modes 86..170

# ── Initial condition ──────────────────────────────────────────────────────────
v0  = 4.0 * np.exp(-((x + 5.0)**2) / 2.25)
u0  = np.zeros(Nx)
v   = v0.copy()
u   = u0.copy()

# ── Precomputed spectral operators ────────────────────────────────────────────
ik    = 1j * k
ik3   = (1j * k)**3
k2    = k**2    # for viscosity: -nu_u * k^2 * u_hat

def rhs(u, v):
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Dealias state before products
    u_hat_d = u_hat * mask
    v_hat_d = v_hat * mask
    u_d = np.fft.ifft(u_hat_d).real
    v_d = np.fft.ifft(v_hat_d).real

    # Derivatives from dealiased state
    u_x   = np.fft.ifft(ik  * u_hat_d).real
    v_x   = np.fft.ifft(ik  * v_hat_d).real
    v_xxx = np.fft.ifft(ik3 * v_hat_d).real

    # u viscosity term: nu_u * u_xx (spectral, from full u_hat not just dealiased)
    u_visc = np.fft.ifft(-nu_u * k2 * u_hat).real

    # u_t = -3 u u_x - 6 v v_x - v_xxx + nu_u * u_xx
    du = -3.0 * u_d * u_x - 6.0 * v_d * v_x - v_xxx + u_visc

    # v_t = -6 v v_x - v_xxx - u_x v - u v_x
    dv = -6.0 * v_d * v_x - v_xxx - u_x * v_d - u_d * v_x

    return du, dv

# ── Snapshot schedule ─────────────────────────────────────────────────────────
snap_times = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
snapshots  = []
snap_idx   = 0

def save_snap(u, v):
    snapshots.append(np.stack([u.copy(), v.copy()], axis=0))

# ── Time integration: explicit RK4 ──────────────────────────────────────────
t = 0.0
save_snap(u, v)   # t=0
snap_idx = 1

for step in range(n_steps):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u +     dt*k3u, v +     dt*k3v)

    u = u + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u)
    v = v + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v)
    t += dt

    # Check for blow-up
    if not np.isfinite(u).all() or not np.isfinite(v).all():
        print(f"BLOW-UP at t={t:.4f}, step={step}")
        save_snap(u, v)
        break

    # Snapshot at scheduled times
    if snap_idx < len(snap_times) and t >= snap_times[snap_idx] - 1e-10:
        save_snap(u, v)
        snap_idx += 1

# ── Diagnostics ───────────────────────────────────────────────────────────────
print(f"t_final = {t:.6f}")
print(f"n_snapshots = {len(snapshots)}")
print(f"all_finite = {np.isfinite(u).all() and np.isfinite(v).all()}")

for i, (t_val) in enumerate([0, 1, 2, 3, 4, 5, 6]):
    if i >= len(snapshots):
        break
    u_s = snapshots[i][0]
    v_s = snapshots[i][1]
    peaks, _ = find_peaks(v_s, prominence=0.1 * max(v_s.max(), 0.5))
    print(f"  t={t_val}: v_max={v_s.max():.3f}, v_min={v_s.min():.3f}, |u|_max={abs(u_s).max():.3f}, n_peaks={len(peaks)}")

if np.isfinite(v).all():
    v_final = v.copy()
    # Detailed peak analysis of final v
    height_thr = 0.8
    peaks_hi, _ = find_peaks(v_final, height=height_thr, prominence=0.3,
                              distance=Nx//20)
    print(f"\nFinal v peaks with amp>=0.8 and prominence>=0.3:")
    print(f"  n_peaks = {len(peaks_hi)}")
    if len(peaks_hi) > 0:
        print(f"  amplitudes = {v_final[peaks_hi]}")
        print(f"  positions  = {x[peaks_hi]}")

    # Mass conservation
    mass0 = np.sum(v0) * (L / Nx)
    massf = np.sum(v_final) * (L / Nx)
    print(f"\nmass_v0 = {mass0:.4f}, mass_vf = {massf:.4f}, drift% = {abs(massf-mass0)/abs(mass0)*100:.3f}%")

# ── Save output ───────────────────────────────────────────────────────────────
out = np.array(snapshots)   # shape (n_snapshots, 2, 256)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_B.npy", out)
print(f"\nSaved shape: {out.shape}")
