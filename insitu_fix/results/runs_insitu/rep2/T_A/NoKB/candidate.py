"""
E3: Coupled Burgers-swept-KdV soliton stability study.
Method: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing,
        CONSERVATION FORM of nonlinear flux.

Change from E2: nonlinear terms in strict conservation form so aliasing
is handled via a single spectral derivative of the flux, not
component-wise product-of-derivative dealiasing.

PDE (conservation form):
  u_t = -d/dx( 3u²/2 + 3v² + v_xx )     [3u u_x = d/dx(3u²/2)]
  v_t = -d/dx( 3v² + u v ) - v_xxx
"""

import numpy as np
import os

# ── Domain ──────────────────────────────────────────────────────────────────
L   = 30.0
Nx  = 256
x   = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# ── Initial conditions ───────────────────────────────────────────────────────
v0  = 2.0 / np.cosh(x + 5.0)**2          # 2 sech²(x+5)
u0  = 0.5 * v0**2 + 0.2 * v0             # v²/2 + 0.2v  (ε=0.2 perturbation)

# ── Wavenumbers (rfft layout) ─────────────────────────────────────────────────
k_r = 2.0 * np.pi / L * np.arange(0, Nx // 2 + 1)
ik  = 1j * k_r
ik2 = ik * ik          # (ik)^2  — for v_xx
ik3 = ik2 * ik         # (ik)^3  — for v_xxx

# 2/3-rule dealiasing mask
cutoff    = Nx // 3    # = 85
mask      = np.arange(Nx // 2 + 1) < cutoff   # True → keep

def spec_d(f):
    """Spectral first derivative d/dx f (dealiased)."""
    return np.fft.irfft(ik * np.where(mask, np.fft.rfft(f), 0.0), n=Nx)

def dealias_hat(fhat):
    return np.where(mask, fhat, 0.0)

# ── RHS in conservation form ─────────────────────────────────────────────────
def rhs(u, v):
    v_hat = dealias_hat(np.fft.rfft(v))
    u_hat = dealias_hat(np.fft.rfft(u))

    # Linear dispersive terms (exact spectral derivatives from dealiased fields)
    v_xx  = np.fft.irfft(ik2 * v_hat, n=Nx)   # v_xx (for u equation flux)
    v_xxx = np.fft.irfft(ik3 * v_hat, n=Nx)   # v_xxx

    # Dealiased physical fields
    u_d   = np.fft.irfft(u_hat, n=Nx)
    v_d   = np.fft.irfft(v_hat, n=Nx)

    # ── u equation: u_t = -d/dx( 3u²/2 + 3v² + v_xx ) ───────────────────
    flux_u       = 1.5 * u_d**2 + 3.0 * v_d**2 + v_xx
    flux_u_hat   = dealias_hat(np.fft.rfft(flux_u))
    du           = -np.fft.irfft(ik * flux_u_hat, n=Nx)

    # ── v equation: v_t = -d/dx( 3v² + u v ) - v_xxx ────────────────────
    flux_v       = 3.0 * v_d**2 + u_d * v_d
    flux_v_hat   = dealias_hat(np.fft.rfft(flux_v))
    dv           = -np.fft.irfft(ik * flux_v_hat, n=Nx) - v_xxx

    return du, dv

# ── Time stepping ─────────────────────────────────────────────────────────────
T_final = 8.0
dt      = 1.0e-4
Nt      = int(round(T_final / dt))
dt      = T_final / Nt

k_max   = np.pi * Nx / L
print(f"Nx={Nx}, dt={dt:.2e}, Nt={Nt}, k_max={k_max:.3f}, |dt*kmax^3|={dt*k_max**3:.3f}")
print(f"Dealiasing cutoff: mode {cutoff} of {Nx//2}")

# ── Snapshot schedule ─────────────────────────────────────────────────────────
n_snaps    = 10
snap_steps = set(int(round(s)) for s in np.linspace(0, Nt, n_snaps))
snapshots  = []

u = u0.copy()
v = v0.copy()

for n in range(Nt + 1):
    if n in snap_steps:
        snapshots.append(np.stack([u.copy(), v.copy()]))

    if n == Nt:
        break

    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u +    dt*k3u,  v +    dt*k3v)

    u += (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v += (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)

    if n % 20000 == 0 and n > 0:
        mu = np.max(np.abs(u))
        mv = np.max(np.abs(v))
        print(f"  n={n:6d}  t={n*dt:.3f}  max|u|={mu:.4f}  max|v|={mv:.4f}")
        if not (np.isfinite(mu) and np.isfinite(mv)):
            print("BLOWUP — stopping early.")
            break

# ── Save output ───────────────────────────────────────────────────────────────
out = np.array(snapshots)
print(f"\nOutput shape  : {out.shape}")
print(f"Final max|u|  : {np.max(np.abs(out[-1, 0])):.4f}")
print(f"Final max|v|  : {np.max(np.abs(out[-1, 1])):.4f}")
print(f"Peak v(T)     : {np.max(out[-1, 1]):.4f}  (need >= 1.0)")
mass0 = np.sum(out[0,  1]) * (L / Nx)
massT = np.sum(out[-1, 1]) * (L / Nx)
print(f"mass(v) t=0   : {mass0:.4f}")
print(f"mass(v) t=T   : {massT:.4f}  (drift {abs(massT-mass0)/abs(mass0)*100:.2f}%)")

# Dominant peak check
v_final = out[-1, 1]
peak_val = np.max(v_final)
peak_idx = np.argmax(v_final)
# check single dominance: no secondary peak > 50% of peak
sorted_v = np.sort(v_final)[::-1]
print(f"10th percentile peak: {sorted_v[9]:.4f} (ratio to peak: {sorted_v[9]/peak_val:.2f})")

os.makedirs('pred_results', exist_ok=True)
np.save('pred_results/T_A.npy', out)
print("Saved  pred_results/T_A.npy")
