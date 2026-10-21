"""
E3: Coupled Burgers-swept-KdV — phase-shifted IC to align oscillation peak with T=8

Method: Fourier pseudospectral + classical RK4 + 2/3-rule dealiasing (same as E1, E2)

IC CHANGE from E2: shift soliton x0 from -5 to -2 (+3 units right).
Rationale: F2 showed v_max=1.154 at T=7.0 but only 0.710 at T=8.0 (oscillation peak
  ~1 time unit before evaluation). KdV soliton speed c ~ 4A/3 = 8/3 ~ 2.67 units/t.
  Shift of +3 spatial units advances the interaction phase by ~3/2.67 ~ 1.12 time units,
  placing the oscillation peak at T~7.0+1.12~8.1 ≈ T=8.

Negative perturbation u0 = 0.5*v0^2 - 0.2*v0 retained from E2 (better than E1).
v0 = 2 * sech^2(x+2), T=8.0, dt=2e-4, Nx=256, domain [-15,15] periodic.
"""

import numpy as np
import os

L = 30.0
Nx = 256
T = 8.0
dt = 2e-4
n_steps = int(round(T / dt))

x = np.linspace(-15.0, 15.0, Nx, endpoint=False)
dx = L / Nx
kx = 2.0 * np.pi * np.fft.fftfreq(Nx, d=dx)
k_idx = np.abs(np.fft.fftfreq(Nx) * Nx)
dealias = (k_idx <= Nx // 3).astype(float)

# E3 IC: soliton at x=-2 (shifted +3 from E2's x=-5), negative perturbation
v = 2.0 / np.cosh(x + 2.0)**2        # v0 = 2*sech^2(x+2)
u = 0.5 * v**2 - 0.2 * v             # u0 = v^2/2 - 0.2*v (m0 = -0.2*v)

print(f"IC: v_max={v.max():.4f} at x={x[np.argmax(v)]:.2f}, u_max={u.max():.4f}")
print(f"    m_max={np.max(u-0.5*v**2):.4f}, m_min={np.min(u-0.5*v**2):.4f}")

def compute_rhs(u, v):
    u_hat = np.fft.fft(u); v_hat = np.fft.fft(v)
    u_hat_d = u_hat * dealias; v_hat_d = v_hat * dealias
    u_d = np.fft.ifft(u_hat_d).real; v_d = np.fft.ifft(v_hat_d).real
    u_x   = np.fft.ifft(1j * kx * u_hat_d).real
    v_x   = np.fft.ifft(1j * kx * v_hat_d).real
    v_xxx = np.fft.ifft((1j * kx)**3 * v_hat_d).real
    rhs_u = -3.0 * u_d * u_x - 6.0 * v_d * v_x - v_xxx
    rhs_v = -6.0 * v_d * v_x - v_xxx - u_x * v_d - u_d * v_x
    return rhs_u, rhs_v

def rk4_step(u, v, dt):
    k1u, k1v = compute_rhs(u, v)
    k2u, k2v = compute_rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = compute_rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = compute_rhs(u + dt*k3u, v + dt*k3v)
    u_new = u + (dt/6.0)*(k1u + 2*k2u + 2*k3u + k4u)
    v_new = v + (dt/6.0)*(k1v + 2*k2v + 2*k3v + k4v)
    return u_new, v_new

n_snapshots = 11
save_every = n_steps // (n_snapshots - 1)   # 4000 steps = 0.8 time units
mass_v0 = np.sum(v) * dx

snapshots_u = [u.copy()]
snapshots_v = [v.copy()]
t_saved = [0.0]

for step in range(1, n_steps + 1):
    u, v = rk4_step(u, v, dt)
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"NaN/Inf at step {step}, t={step*dt:.4f}")
        break
    if step % save_every == 0:
        t_now = step * dt
        snapshots_u.append(u.copy())
        snapshots_v.append(v.copy())
        t_saved.append(t_now)
        mass_v = np.sum(v) * dx
        print(f"t={t_now:.2f}  v_max={v.max():.4f}  u_max={np.abs(u).max():.4f}  "
              f"mass_drift%={(abs(mass_v-mass_v0)/abs(mass_v0))*100:.4f}%")

result = np.stack([np.array(snapshots_u), np.array(snapshots_v)], axis=1)
print(f"\nOutput shape: {result.shape}")
print(f"Final v_max: {snapshots_v[-1].max():.4f}  (initial: {snapshots_v[0].max():.4f})")
print(f"Retention: {snapshots_v[-1].max()/snapshots_v[0].max()*100:.1f}%")
print(f"Final u_max: {np.abs(snapshots_u[-1]).max():.4f}")
mass_v_final = np.sum(snapshots_v[-1]) * dx
print(f"Mass drift: {abs(mass_v_final-mass_v0)/abs(mass_v0)*100:.4f}%")

os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_A.npy', result)
print("Saved pred_results/T_A.npy")
