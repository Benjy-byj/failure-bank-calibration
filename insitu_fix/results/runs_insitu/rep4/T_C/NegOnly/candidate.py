"""
E2: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4.
dt=1e-4 (reduced from E1 to stabilize bore steepening).
nu_u=5e-2 linear viscosity on u-equation (per BKdV-S6 deep synthesis recommendation).

PDE (flux form):
  u_t = -d_x(3*u^2/2 + 3*v^2) - v_xxx  + nu_u * u_xx
  v_t = -d_x(3*v^2 + u*v)    - v_xxx

In Fourier space:
  u_hat_t = ik^3 * v_hat - ik * fft(3*u^2/2 + 3*v^2) - nu_u*k^2 * u_hat
  v_hat_t = ik^3 * v_hat - ik * fft(3*v^2 + u*v)
  [+ik^3 comes from -v_xxx = -(ik)^3*v_hat = +ik^3*v_hat since (ik)^3=-ik^3]
"""
import numpy as np
import os

# ── Parameters ──────────────────────────────────────────────────────────────
Nx   = 256
L    = 30.0      # domain [-15, 15]
T    = 8.0
dt   = 1e-4      # reduced from 2e-4 for bore-IC stability
nu_u = 5e-2      # linear viscosity on u-equation (BKdV-S6 recommendation)

n_steps = int(round(T / dt))   # 80000 steps

# ── Grid and wavenumbers ─────────────────────────────────────────────────────
x     = np.linspace(-15.0, 15.0, Nx, endpoint=False)
k_int = np.fft.fftfreq(Nx, d=1.0 / Nx)   # integer mode indices
k     = 2.0 * np.pi / L * k_int           # physical wavenumbers (rad/m)
k2    = k**2
k3    = k**3

# 2/3 dealiasing mask
dealias = (np.abs(k_int) <= Nx // 3).astype(float)

# ── Initial conditions ───────────────────────────────────────────────────────
u = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # smoothed bore: u_L=1.5, u_R=0
v = 1.5 / np.cosh(x + 8.0)**2              # KdV soliton at x=-8, amplitude 1.5

# ── RHS function ─────────────────────────────────────────────────────────────
def rhs(u, v):
    u_hat = np.fft.fft(u)
    v_hat = np.fft.fft(v)

    # Dealiased physical fields
    u_d = np.real(np.fft.ifft(dealias * u_hat))
    v_d = np.real(np.fft.ifft(dealias * v_hat))

    # Dealiased nonlinear fluxes
    flux_u_hat = dealias * np.fft.fft(1.5 * u_d**2 + 3.0 * v_d**2)
    flux_v_hat = dealias * np.fft.fft(3.0 * v_d**2 + u_d * v_d)

    # Time derivatives in Fourier space
    # +ik^3*v_hat : dispersive term (-v_xxx moved to RHS)
    # -ik*flux  : nonlinear flux divergence
    # -nu_u*k^2*u_hat : explicit linear viscosity on u (damps bore Gibbs oscillations)
    du_hat = 1j * k3 * v_hat - 1j * k * flux_u_hat - nu_u * k2 * u_hat
    dv_hat = 1j * k3 * v_hat - 1j * k * flux_v_hat

    return np.real(np.fft.ifft(du_hat)), np.real(np.fft.ifft(dv_hat))

# ── Snapshot schedule ─────────────────────────────────────────────────────────
# 9 snapshots at t = 0, 1, 2, 3, 4, 5, 6, 7, 8
t_snap   = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
snap_set = set(int(round(t / dt)) for t in t_snap)

snapshots = []

# ── Time integration (RK4) ────────────────────────────────────────────────────
for step in range(n_steps + 1):
    if step in snap_set:
        snapshots.append(np.stack([u.copy(), v.copy()]))
        print(f"t={step*dt:.2f}: u_max={u.max():.4f} u_min={u.min():.4f} "
              f"v_max={v.max():.4f} finite={np.isfinite(u).all() and np.isfinite(v).all()}")

    if step >= n_steps:
        break

    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)

    u += dt / 6.0 * (k1u + 2*k2u + 2*k3u + k4u)
    v += dt / 6.0 * (k1v + 2*k2v + 2*k3v + k4v)

# ── Save output ───────────────────────────────────────────────────────────────
output = np.array(snapshots)   # shape: (9, 2, 256)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", output)
print(f"\nSaved: shape={output.shape}, finite={np.isfinite(output).all()}")
print(f"Final: u_max={output[-1,0].max():.4f}, u_min={output[-1,0].min():.4f}, "
      f"v_max={output[-1,1].max():.4f}")
print(f"mass_u={np.trapz(output[-1,0], x):.6f}, mass_v={np.trapz(output[-1,1], x):.6f}")
