"""
E1 (bug-fix): Coupled Burgers-swept-KdV — Fourier pseudospectral + 2/3-rule dealiasing + classical RK4
Bug fix: apply dealias mask to state AFTER each RK4 step to prevent ghost high-k accumulation in uhat.
PDE:
  u_t + 3*u*u_x = -d_x(3*v^2 + v_xx)
  v_t + 6*v*v_x + v_xxx = -d_x(u*v)
IC: v = 4*exp(-(x+5)^2/2.25), u = 0
Domain: x in [-15,15], periodic, Nx=256, T=6
"""
import numpy as np
import os

# ------------------------------------------------------------------
# Parameters
# ------------------------------------------------------------------
L = 30.0
Nx = 256
x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dt = 1e-4
T = 6.0

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0/Nx)

# 2/3-rule dealiasing mask: zero modes with |k| > (2/3)*k_Nyquist
k_Nyquist = np.pi * Nx / L   # = pi/dx
dealias = (np.abs(k) <= (2.0 / 3.0) * k_Nyquist)

# Pre-compute spectral operators
ik = 1j * k           # spectral d/dx
ik3 = 1j * (k ** 3)  # -(ik)^3 = i*k^3, used for the -v_xxx term

# ------------------------------------------------------------------
# Initial condition
# ------------------------------------------------------------------
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros(Nx)

uhat = np.fft.fft(u0)
vhat = np.fft.fft(v0)

# Apply initial dealias (u0=0 so trivial, v0 smooth so also trivial)
uhat = dealias * uhat
vhat = dealias * vhat

# ------------------------------------------------------------------
# RHS function (operates in spectral space)
# ------------------------------------------------------------------
def rhs(uhat, vhat):
    """
    Returns d/dt [uhat, vhat] for the coupled BKdV system.
    Inputs MUST already have ghost modes zeroed (dealias applied).
    """
    # Physical-space fields from dealiased spectral state
    u = np.real(np.fft.ifft(uhat))
    v = np.real(np.fft.ifft(vhat))

    # Nonlinear products (alias-free since u, v are N/3-bandlimited)
    u2hat = np.fft.fft(u * u)
    v2hat = np.fft.fft(v * v)
    uvhat = np.fft.fft(u * v)

    # u_t = -(3/2)*(u^2)_x - 3*(v^2)_x - v_xxx
    #      = -ik*(1.5*u2 + 3*v2) + ik3*v
    duhat_dt = -ik * (1.5 * u2hat + 3.0 * v2hat) + ik3 * vhat

    # v_t = -3*(v^2)_x - (u*v)_x - v_xxx
    #      = -ik*(3*v2 + uv) + ik3*v
    dvhat_dt = -ik * (3.0 * v2hat + uvhat) + ik3 * vhat

    return duhat_dt, dvhat_dt

# ------------------------------------------------------------------
# Classical RK4 step with dealiasing of intermediate and final states
# ------------------------------------------------------------------
def rk4_step(uhat, vhat, dt):
    # Intermediate stages: apply dealias to maintain band-limit
    k1u, k1v = rhs(uhat, vhat)

    uh2 = dealias * (uhat + 0.5*dt*k1u)
    vh2 = dealias * (vhat + 0.5*dt*k1v)
    k2u, k2v = rhs(uh2, vh2)

    uh3 = dealias * (uhat + 0.5*dt*k2u)
    vh3 = dealias * (vhat + 0.5*dt*k2v)
    k3u, k3v = rhs(uh3, vh3)

    uh4 = dealias * (uhat + dt*k3u)
    vh4 = dealias * (vhat + dt*k3v)
    k4u, k4v = rhs(uh4, vh4)

    uhat_new = dealias * (uhat + (dt/6.0) * (k1u + 2*k2u + 2*k3u + k4u))
    vhat_new = dealias * (vhat + (dt/6.0) * (k1v + 2*k2v + 2*k3v + k4v))
    return uhat_new, vhat_new

# ------------------------------------------------------------------
# Snapshot storage
# ------------------------------------------------------------------
n_snapshots = 10
t_save = np.linspace(0.0, T, n_snapshots)
snapshots = np.zeros((n_snapshots, 2, Nx))
snapshots[0, 0] = u0
snapshots[0, 1] = v0
snap_idx = 1

# ------------------------------------------------------------------
# Time integration
# ------------------------------------------------------------------
t = 0.0
n_steps = int(round(T / dt))
check_every = 5000

print(f"Running: Nx={Nx}, dt={dt}, T={T}, n_steps={n_steps}")
print(f"CFL check: dt*k_eff^3 = {dt * (2/3 * k_Nyquist)**3:.4f} (limit: 2.83)")

for step in range(n_steps):
    uhat, vhat = rk4_step(uhat, vhat, dt)
    t += dt

    # Save snapshot
    if snap_idx < n_snapshots and t >= t_save[snap_idx] - 0.5 * dt:
        u_phys = np.real(np.fft.ifft(uhat))
        v_phys = np.real(np.fft.ifft(vhat))
        snapshots[snap_idx, 0] = u_phys
        snapshots[snap_idx, 1] = v_phys
        snap_idx += 1

    # Blow-up check and progress
    if step % check_every == 0:
        u_phys = np.real(np.fft.ifft(uhat))
        v_phys = np.real(np.fft.ifft(vhat))
        if not (np.isfinite(u_phys).all() and np.isfinite(v_phys).all()):
            print(f"BLOW-UP at step={step}, t={t:.4f}")
            break
        print(f"  step={step:6d}, t={t:.4f}, |v|_max={v_phys.max():.4f}, |u|_max={u_phys.max():.4f}")

# Fill remaining snapshot slots
u_final = np.real(np.fft.ifft(uhat))
v_final = np.real(np.fft.ifft(vhat))
while snap_idx < n_snapshots:
    snapshots[snap_idx, 0] = u_final
    snapshots[snap_idx, 1] = v_final
    snap_idx += 1

# ------------------------------------------------------------------
# Save output
# ------------------------------------------------------------------
os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', snapshots)
print(f"\n=== DONE ===")
print(f"Saved: shape={snapshots.shape}")
print(f"Final t={t:.6f}")
print(f"v_final: max={v_final.max():.4f}, min={v_final.min():.4f}")
print(f"u_final: max={u_final.max():.4f}, min={u_final.min():.4f}")

# Mass conservation
mass_v0 = np.sum(v0) * (L / Nx)
mass_vf = np.sum(v_final) * (L / Nx)
drift_pct = abs(mass_vf - mass_v0) / abs(mass_v0) * 100
print(f"Mass v: initial={mass_v0:.4f}, final={mass_vf:.4f}, drift={drift_pct:.3f}%")

# High-k energy fractions
vhat_f = np.fft.fft(v_final)
uhat_f = np.fft.fft(u_final)
frac_v_high = np.sum(np.abs(vhat_f[~dealias])**2) / np.sum(np.abs(vhat_f)**2)
frac_u_high = np.sum(np.abs(uhat_f[~dealias])**2) / np.sum(np.abs(uhat_f)**2) if np.sum(np.abs(uhat_f)**2)>0 else 0
print(f"High-k fraction: v={frac_v_high:.4f}, u={frac_u_high:.4f}")

# TV
TV_u = np.sum(np.abs(np.diff(u_final)))
TV_v = np.sum(np.abs(np.diff(v_final)))
print(f"TV: u={TV_u:.2f}, v={TV_v:.2f}")

# Peak detection
from scipy.signal import find_peaks
peaks_hi, _ = find_peaks(v_final, height=0.8, distance=5)
print(f"\nHigh peaks in v (height>=0.8, dist>=5): {len(peaks_hi)}")
if len(peaks_hi) > 0:
    amps = v_final[peaks_hi]
    pos  = x[peaks_hi]
    sort_idx = np.argsort(pos)
    gaps = np.diff(pos[sort_idx])
    print(f"Amplitudes: {amps.round(3)}")
    print(f"Positions:  {pos.round(3)}")
    print(f"Inter-peak gaps (min={gaps.min():.3f}): {gaps.round(3)}")
