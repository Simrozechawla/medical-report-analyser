import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ecg.digitize import digitize


def make_test_image(path="data/samples/test_ecg.png"):
    """Generate a synthetic ECG image for testing."""
    t   = np.linspace(0, 5, 2500)
    sig = np.zeros_like(t)
    for beat in np.arange(0.1, 5.0, 60/72):
        sig += 0.15 * np.exp(-((t - beat - 0.08)**2) / (2*0.018**2))
        sig -= 0.10 * np.exp(-((t - beat - 0.175)**2) / (2*0.008**2))
        sig += 1.20 * np.exp(-((t - beat - 0.200)**2) / (2*0.010**2))
        sig -= 0.18 * np.exp(-((t - beat - 0.225)**2) / (2*0.008**2))
        sig += 0.30 * np.exp(-((t - beat - 0.370)**2) / (2*0.038**2))
    sig += np.random.normal(0, 0.015, len(t))

    fig, ax = plt.subplots(figsize=(14, 4), dpi=120)
    ax.set_facecolor("#FFF4F4")
    ax.set_xticks(np.arange(0, 5.2, 0.04), minor=True)
    ax.set_yticks(np.arange(-0.6, 1.8, 0.10), minor=True)
    ax.grid(which="minor", color="#FFB3B3", linewidth=0.4, alpha=0.9)
    ax.set_xticks(np.arange(0, 5.2, 0.2))
    ax.set_yticks(np.arange(-0.5, 1.6, 0.5))
    ax.grid(which="major", color="#FF6060", linewidth=0.9, alpha=0.7)
    ax.plot(t, sig, color="black", linewidth=1.1)
    ax.set_xlim(0, 5); ax.set_ylim(-0.6, 1.6)
    plt.tight_layout()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"Test image saved → {path}")


if __name__ == "__main__":
    make_test_image()
    peaks, signal, hr = digitize("data/samples/test_ecg.png")
    print(f"Beats detected : {len(peaks)}")
    print(f"Heart rate     : {hr} bpm  (expected ~72)")