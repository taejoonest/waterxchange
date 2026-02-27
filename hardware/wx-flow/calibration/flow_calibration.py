"""
WX-Flow Heat Pulse Calibration Script

Generates calibration curves from lab test data. You run the probe in a
controlled flow column at known velocities and record the peak delay times.
This script fits the v = K / t_peak relationship and outputs the K constant
for config.h.

Usage:
    python flow_calibration.py --data calibration_data.csv

CSV format:
    known_velocity_cm_day, peak_delay_seconds
    10.0, 45.2
    25.0, 18.1
    50.0, 9.0
    100.0, 4.5
    ...
"""

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import curve_fit


def inverse_model(t, K):
    """v = K / t"""
    return K / t


def load_data(csv_path: str):
    velocities = []
    delays = []
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            try:
                v = float(row[0].strip())
                t = float(row[1].strip())
                if t > 0 and v > 0:
                    velocities.append(v)
                    delays.append(t)
            except (ValueError, IndexError):
                continue
    return np.array(velocities), np.array(delays)


def calibrate(velocities, delays):
    popt, pcov = curve_fit(inverse_model, delays, velocities, p0=[500.0])
    K = popt[0]
    perr = np.sqrt(np.diag(pcov))[0]
    predicted = inverse_model(delays, K)
    residuals = velocities - predicted
    r_squared = 1 - np.sum(residuals**2) / np.sum((velocities - np.mean(velocities))**2)
    return K, perr, r_squared, predicted


def main():
    parser = argparse.ArgumentParser(description='WX-Flow heat pulse calibration')
    parser.add_argument('--data', required=True, help='Path to calibration CSV')
    parser.add_argument('--plot', action='store_true', help='Show calibration plot')
    args = parser.parse_args()

    if not Path(args.data).exists():
        print(f"File not found: {args.data}")
        sys.exit(1)

    velocities, delays = load_data(args.data)
    if len(velocities) < 3:
        print(f"Need at least 3 data points, got {len(velocities)}")
        sys.exit(1)

    K, K_err, r2, predicted = calibrate(velocities, delays)

    print(f"\n{'='*50}")
    print(f"  WX-Flow Heat Pulse Calibration Results")
    print(f"{'='*50}")
    print(f"  Data points:     {len(velocities)}")
    print(f"  Model:           v = K / t_peak")
    print(f"  K constant:      {K:.1f} ± {K_err:.1f} cm·s/day")
    print(f"  R² :             {r2:.4f}")
    print(f"{'='*50}")
    print(f"\n  → Set FLOW_CAL_K to {K:.1f} in config.h\n")

    print("  Actual vs Predicted:")
    print(f"  {'Actual (cm/d)':>14} {'Delay (s)':>10} {'Predicted':>12} {'Error %':>10}")
    for v, t, p in zip(velocities, delays, predicted):
        err_pct = abs(v - p) / v * 100
        print(f"  {v:>14.1f} {t:>10.1f} {p:>12.1f} {err_pct:>9.1f}%")

    if args.plot:
        try:
            import matplotlib.pyplot as plt

            t_fit = np.linspace(min(delays) * 0.8, max(delays) * 1.2, 100)
            v_fit = inverse_model(t_fit, K)

            plt.figure(figsize=(8, 5))
            plt.scatter(delays, velocities, c='#0e9aa7', s=80, zorder=5, label='Lab data')
            plt.plot(t_fit, v_fit, 'k--', label=f'v = {K:.0f}/t  (R²={r2:.3f})')
            plt.xlabel('Peak Delay Time (seconds)')
            plt.ylabel('Flow Velocity (cm/day)')
            plt.title('WX-Flow Heat Pulse Calibration')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig('calibration_curve.png', dpi=150)
            plt.show()
            print("  Plot saved to calibration_curve.png")
        except ImportError:
            print("  Install matplotlib for plotting: pip install matplotlib")


if __name__ == '__main__':
    main()
