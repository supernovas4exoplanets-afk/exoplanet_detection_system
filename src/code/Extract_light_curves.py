import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from astropy.timeseries import BoxLeastSquares
from scipy.signal import savgol_filter
import os
import re
import glob

# ==========================================
# Directory Setup
# ==========================================
base_dir = os.path.expanduser("~/Downloads/s0002/target/0000/0001")
output_dir = os.path.expanduser("~/Downloads/light_curves")
os.makedirs(output_dir, exist_ok=True)

# Find all .fits files recursively under base_dir
fits_files = glob.glob(os.path.join(base_dir, "**", "*.fits"), recursive=True)
print(f"Found {len(fits_files)} FITS files")

# ==========================================
# Process Each File
# ==========================================
for fits_path in fits_files:
    filename = os.path.basename(fits_path)

    # Extract TIC ID from filename (e.g., hlsp_tess-spoc_tess_phot_0000000177020632-s0002_....
    # Extract TIC ID: find the segment matching digits followed by -sNNNN
    match = re.search(r'_(\d+)-s\d+_', filename)
    if match:
        tic_id = match.group(1).lstrip("0") or "0"
    else:
        print(f"Could not extract TIC ID from {filename}, skipping")
        continue

    print(f"\nProcessing TIC {tic_id} — {filename}")

    # ==========================================
    # Load FITS light curve
    # ==========================================
    try:
        with fits.open(fits_path) as hdul:
            data = hdul[1].data
            time = data["TIME"]
            flux = data["PDCSAP_FLUX"]
    except Exception as e:
        print(f"  Failed to read {filename}: {e}")
        continue

    # ==========================================
    # Remove NaNs
    # ==========================================
    mask = np.isfinite(time) & np.isfinite(flux)
    time = time[mask]
    flux = flux[mask]

    if len(time) < 100:
        print(f"  Too few data points ({len(time)}), skipping")
        continue

    # ==========================================
    # Normalize
    # ==========================================
    flux = flux / np.median(flux)

    # ==========================================
    # Flatten (Detrend)
    # ==========================================
    # Window must be odd and less than data length
    window = min(301, len(flux) - (1 if len(flux) % 2 == 0 else 0))
    if window % 2 == 0:
        window -= 1
    trend = savgol_filter(flux, window, 2)
    flat_flux = flux / trend

    # ==========================================
    # BLS Search
    # ==========================================
    bls = BoxLeastSquares(time, flat_flux)
    period_grid = np.linspace(0.5, 20, 10000)
    duration_grid = np.linspace(0.05, 0.3, 10)
    power = bls.power(period_grid, duration_grid)

    # ==========================================
    # Best Candidate
    # ==========================================
    best_idx = np.argmax(power.power)
    best_period = power.period[best_idx]
    best_duration = power.duration[best_idx]
    best_t0 = power.transit_time[best_idx]

    print(f"  Period: {best_period:.4f} d | Duration: {best_duration:.4f} d | T0: {best_t0:.4f}")

    # ==========================================
    # Fold Light Curve
    # ==========================================
    phase = ((time - best_t0 + 0.5 * best_period) % best_period) - 0.5 * best_period
    phase /= best_period

    # ==========================================
    # Save Flattened Light Curve
    # ==========================================
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(time, flat_flux, ".", ms=1)
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Normalized Flux")
    ax.set_title(f"Flattened Light Curve — TIC {tic_id}")
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, f"TIC_{tic_id}_flattened.png"), dpi=150)
    plt.close(fig)

    # ==========================================
    # Save BLS Periodogram
    # ==========================================
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(power.period, power.power)
    ax.axvline(best_period, color="r", lw=1, linestyle="--", label=f"Best: {best_period:.4f} d")
    ax.set_xlabel("Period (days)")
    ax.set_ylabel("BLS Power")
    ax.set_title(f"BLS Periodogram — TIC {tic_id}")
    ax.legend()
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, f"TIC_{tic_id}_bls.png"), dpi=150)
    plt.close(fig)

    # ==========================================
    # Save Phase Folded Light Curve
    # ==========================================
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(phase, flat_flux, ".", ms=1, alpha=0.5)
    ax.set_xlabel("Phase")
    ax.set_ylabel("Normalized Flux")
    ax.set_title(f"Phase Folded Light Curve — TIC {tic_id}\nPeriod = {best_period:.4f} d")
    ax.set_xlim(-0.5, 0.5)
    plt.tight_layout()
    fig.savefig(os.path.join(output_dir, f"TIC_{tic_id}_phase.png"), dpi=150)
    plt.close(fig)

    print(f"  Saved → TIC_{tic_id}_flattened.png, TIC_{tic_id}_bls.png, TIC_{tic_id}_phase.png")

print("\nDone.")
