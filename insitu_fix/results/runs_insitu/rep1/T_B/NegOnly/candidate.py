"""
E1: Fourier pseudospectral + 2/3-rule dealiasing + classical RK4 (fully explicit).
PDE:
  u_t = -3*u*u_x - 6*v*v_x - v_xxx
  v_t = -6*v*v_x - v_xxx - u_x*v - u*v_x
Domain: x in [-15, 15], Nx=256, T=6.0, dt=2e-4.
IC: v0 = 4*exp(-((x+5)^2)/2.25), u0 = 0.
"""
import numpy as np
import os

# ── Grid ──────────────────────────────────────────────────────────────────────
L = 30.0
Nx = 256
T = 6.0
dt = 2.0e-4

x = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers (numpy fftfreq ordering)
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx) * Nx

# 2/3-rule dealiasing mask: zero modes with |k_index| > Nx//3
k_int = np.abs(np.fft.fftfreq(Nx) * Nx)  # integer wavenumber magnitude
dealias = (k_int <= Nx // 3).astype(float)   # 1 for |k_idx|<=85, 0 otherwise


# ── RHS in spectral space ─────────────────────────────────────────────────────
def rhs(uh, vh):
    """
    uh, vh : dealiased spectral coefficients.
    Returns duh, dvh (spectral RHS).
    """
    # Physical-space fields (already dealiased)
    u   = np.fft.ifft(uh).real
    v   = np.fft.ifft(vh).real
    u_x = np.fft.ifft(1j * k * uh).real
    v_x = np.fft.ifft(1j * k * vh).real

    # Dispersive term: (ik)^3 * vh = spectral coefficient of v_xxx
    disp = (1j * k)**3 * vh   # (ik)^3 = -ik^3

    # Nonlinear products in physical space
    nl_u = -3.0 * u * u_x - 6.0 * v * v_x            # excludes -v_xxx
    nl_v = -6.0 * v * v_x - (u_x * v + u * v_x)      # excludes -v_xxx

    # Transform back to spectral and apply 2/3 dealiasing to nonlinear part
    nl_u_hat = np.fft.fft(nl_u) * dealias
    nl_v_hat = np.fft.fft(nl_v) * dealias

    # Full spectral RHS
    duh = nl_u_hat - disp
    dvh = nl_v_hat - disp
    return duh, dvh


# ── Initial conditions ────────────────────────────────────────────────────────
v0 = 4.0 * np.exp(-((x + 5.0) ** 2) / 2.25)
u0 = np.zeros(Nx)

u_hat = np.fft.fft(u0) * dealias
v_hat = np.fft.fft(v0) * dealias


# ── Time-stepping (classical RK4) ─────────────────────────────────────────────
n_steps = int(round(T / dt))           # 30 000
n_snaps  = 10                          # snapshot intervals (plus t=0 → 11 total)
snap_at  = set(int(round(i * n_steps / n_snaps)) for i in range(n_snaps + 1))

snapshots = []

print(f"n_steps={n_steps}, dt={dt:.1e}, T={T}")
print(f"Post-dealias k_max = {(2.0/3)*np.pi*Nx/L:.3f}, CFL_disp = {2.828/((2.0/3*np.pi*Nx/L)**3):.4e}")

for step in range(n_steps + 1):
    # ── snapshot ──
    if step in snap_at:
        u = np.fft.ifft(u_hat).real
        v = np.fft.ifft(v_hat).real
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
            print(f"NaN/Inf detected at step {step}, t={step*dt:.4f} — aborting.")
            raise RuntimeError("Blow-up")
        snapshots.append(np.stack([u, v]))
        t = step * dt
        mass_v = np.trapezoid(v, x)
        # quick peak count in v
        lm = np.where((v[1:-1] > v[:-2]) & (v[1:-1] > v[2:]))[0] + 1
        big = lm[v[lm] >= 0.8] if len(lm) else np.array([], dtype=int)
        print(f"  t={t:.2f}: v_max={v.max():.4f}  u_max={u.max():.4f}"
              f"  mass_v={mass_v:.4f}  peaks>=0.8: {len(big)}")

    if step == n_steps:
        break

    # ── RK4 substeps ──
    k1u, k1v = rhs(u_hat, v_hat)

    uh2 = (u_hat + 0.5 * dt * k1u) * dealias
    vh2 = (v_hat + 0.5 * dt * k1v) * dealias
    k2u, k2v = rhs(uh2, vh2)

    uh3 = (u_hat + 0.5 * dt * k2u) * dealias
    vh3 = (v_hat + 0.5 * dt * k2v) * dealias
    k3u, k3v = rhs(uh3, vh3)

    uh4 = (u_hat + dt * k3u) * dealias
    vh4 = (v_hat + dt * k3v) * dealias
    k4u, k4v = rhs(uh4, vh4)

    u_hat = (u_hat + (dt / 6.0) * (k1u + 2*k2u + 2*k3u + k4u)) * dealias
    v_hat = (v_hat + (dt / 6.0) * (k1v + 2*k2v + 2*k3v + k4v)) * dealias


# ── Save output ───────────────────────────────────────────────────────────────
result = np.array(snapshots)   # shape (11, 2, 256)
print(f"\nOutput shape: {result.shape}")
print(f"All finite: {np.all(np.isfinite(result))}")

# Final diagnostics
v_final = result[-1, 1]
v_init  = result[0,  1]
mass_i  = np.trapezoid(v_init,  x)
mass_f  = np.trapezoid(v_final, x)
print(f"mass_v: {mass_i:.4f} → {mass_f:.4f}  (drift {abs(mass_f-mass_i)/abs(mass_i)*100:.2f}%)")

lm = np.where((v_final[1:-1] > v_final[:-2]) & (v_final[1:-1] > v_final[2:]))[0] + 1
big = lm[v_final[lm] >= 0.8]
print(f"Final v local maxima >= 0.8: {len(big)}")
if len(big):
    print(f"  at x = {x[big]}, amp = {v_final[big]}")

os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_B.npy', result)
print("Saved pred_results/T_B.npy")
