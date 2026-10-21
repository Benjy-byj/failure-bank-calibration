"""
E2: Fourier pseudospectral + explicit RK4 + 2/3-rule dealiasing.
Single upgrade vs E1: add Orszag 2/3-rule dealiasing to suppress aliasing
in all nonlinear products (u^2, v^2, uv).

Coupled Burgers-swept-KdV (conservative form):
  u_t = -d/dx[(3/2)u^2 + 3v^2 + v_xx]
  v_t = -d/dx[3v^2 + uv] - v_xxx
"""

import numpy as np
import os

# ── Domain ──────────────────────────────────────────────────────────────────
L  = 30.0
Nx = 256
x  = np.linspace(-15.0, 15.0, Nx, endpoint=False)

# Wavenumbers
k = 2.0 * np.pi / L * np.fft.fftfreq(Nx, d=1.0 / Nx)

# 2/3-rule dealiasing mask: zero out modes with |n| > Nx/3
# In fft ordering: n goes 0,1,...,Nx/2,-Nx/2+1,...,-1
dealias_mask = np.ones(Nx, dtype=float)
n = np.fft.fftfreq(Nx, d=1.0 / Nx)   # integer mode indices
dealias_mask[np.abs(n) > Nx // 3] = 0.0

# ── Initial conditions ───────────────────────────────────────────────────────
u0 = 1.5 * (1.0 - np.tanh(x / 0.5)) / 2.0   # bore: u_L=1.5, u_R=0
v0 = 1.5 / np.cosh(x + 8.0) ** 2             # KdV soliton at x=-8, amp=1.5

# ── Dealiased FFT helpers ────────────────────────────────────────────────────
def fft_d(f):
    """FFT with 2/3-rule dealiasing applied."""
    return np.fft.fft(f) * dealias_mask

def product_d(a, b):
    """Dealiased product: compute a*b in physical space from their dealiased spectra."""
    # Both a,b are already in physical space; transform, dealias, multiply, return physical
    ahat = fft_d(a)
    bhat = fft_d(b)
    a_d  = np.real(np.fft.ifft(ahat))
    b_d  = np.real(np.fft.ifft(bhat))
    return a_d * b_d   # product in physical space

# ── RHS ─────────────────────────────────────────────────────────────────────
def rhs(u, v):
    uhat = np.fft.fft(u)
    vhat = np.fft.fft(v)

    # Linear spectral derivatives (no dealiasing needed for linear terms)
    vxx_hat  = -k**2       * vhat
    vxxx_hat = -1j * k**3  * vhat
    vxx      = np.real(np.fft.ifft(vxx_hat))
    vxxx     = np.real(np.fft.ifft(vxxx_hat))

    # Dealiased nonlinear products
    u2   = product_d(u, u)        # u^2
    v2   = product_d(v, v)        # v^2
    uv   = product_d(u, v)        # u*v

    # Fluxes
    flux_u = 1.5 * u2 + 3.0 * v2 + vxx
    flux_v = 3.0 * v2 + uv

    # Spatial derivatives of fluxes (dealiased)
    dudt = -np.real(np.fft.ifft(1j * k * fft_d(flux_u)))
    dvdt = -np.real(np.fft.ifft(1j * k * fft_d(flux_v))) - vxxx

    return dudt, dvdt

# ── RK4 step ────────────────────────────────────────────────────────────────
def rk4_step(u, v, dt):
    k1u, k1v = rhs(u, v)
    k2u, k2v = rhs(u + 0.5*dt*k1u, v + 0.5*dt*k1v)
    k3u, k3v = rhs(u + 0.5*dt*k2u, v + 0.5*dt*k2v)
    k4u, k4v = rhs(u + dt*k3u,     v + dt*k3v)
    u_new = u + (dt / 6.0) * (k1u + 2.0*k2u + 2.0*k3u + k4u)
    v_new = v + (dt / 6.0) * (k1v + 2.0*k2v + 2.0*k3v + k4v)
    return u_new, v_new

# ── Simulation ───────────────────────────────────────────────────────────────
T      = 8.0
dt     = 1e-4
nt     = int(round(T / dt))      # 80 000 steps

n_snapshots = 10
snap_steps  = set(np.round(np.linspace(0, nt, n_snapshots)).astype(int))

u = u0.copy()
v = v0.copy()
snapshots = []

for step in range(nt + 1):
    if step in snap_steps:
        snapshots.append(np.stack([u, v], axis=0))

    if step == nt:
        break

    u, v = rk4_step(u, v, dt)

    # Blow-up guard
    if not (np.all(np.isfinite(u)) and np.all(np.isfinite(v))):
        print(f"NaN/Inf at step {step}, t={step*dt:.4f}")
        break
    if np.max(np.abs(u)) > 200 or np.max(np.abs(v)) > 200:
        print(f"Amplitude blow-up at step {step}, t={step*dt:.4f}")
        break

# ── Save ─────────────────────────────────────────────────────────────────────
snap_array = np.array(snapshots)   # (n_snapshots, 2, Nx)
os.makedirs("pred_results", exist_ok=True)
np.save("pred_results/T_C.npy", snap_array)

# Diagnostics
t_final = step * dt
print(f"Steps run:   {step}")
print(f"t_final:     {t_final:.4f}")
print(f"Snapshots:   {snap_array.shape}")
print(f"u ∈ [{u.min():.4f}, {u.max():.4f}]   |u|_max = {np.max(np.abs(u)):.4f}")
print(f"v ∈ [{v.min():.4f}, {v.max():.4f}]   peak    = {v.max():.4f}")
u_mass = np.sum(u) * (L / Nx)
v_mass = np.sum(v) * (L / Nx)
print(f"∫u dx = {u_mass:.4f}   ∫v dx = {v_mass:.4f}")
print(f"Saved to pred_results/T_C.npy")
