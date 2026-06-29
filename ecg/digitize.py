import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt, find_peaks


def remove_grid(img_bgr):
    """Remove the pink/red ECG grid, leave only the black trace."""
    img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    lower_red1 = np.array([0,   20, 150])
    upper_red1 = np.array([15, 255, 255])
    lower_red2 = np.array([155, 20, 150])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(img_hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(img_hsv, lower_red2, upper_red2)

    lower_bg = np.array([0,  5, 240])
    upper_bg = np.array([20, 60, 255])
    bg_mask  = cv2.inRange(img_hsv, lower_bg, upper_bg)

    full_mask = cv2.bitwise_or(cv2.bitwise_or(mask1, mask2), bg_mask)

    img_clean = img_bgr.copy()
    img_clean[full_mask > 0] = [255, 255, 255]
    return img_clean, full_mask


def extract_trace(img_clean_bgr):
    """For each pixel column, find where the black trace is."""
    gray = cv2.cvtColor(img_clean_bgr, cv2.COLOR_BGR2GRAY)
    _, trace_mask = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    kernel = np.ones((2, 2), np.uint8)
    trace_mask = cv2.morphologyEx(trace_mask, cv2.MORPH_OPEN, kernel)

    height, width = trace_mask.shape
    xs, ys = [], []
    for x in range(width):
        col = trace_mask[:, x]
        dark_rows = np.where(col > 0)[0]
        if len(dark_rows) > 0:
            xs.append(x)
            ys.append(height - np.mean(dark_rows))  # flip y axis

    xs = np.array(xs, dtype=float)
    ys = np.array(ys, dtype=float)
    ys = (ys - ys.min()) / (ys.max() - ys.min() + 1e-9)  # normalize 0-1
    return xs, ys, trace_mask


def pan_tompkins(signal, fs):
    """Detect R-peaks (heartbeats) in a 1D signal."""
    nyq = fs / 2.0
    b, a = butter(2, [5.0 / nyq, 15.0 / nyq], btype='band')
    filtered   = filtfilt(b, a, signal)
    squared    = np.gradient(filtered) ** 2
    window     = max(1, int(0.15 * fs))
    integrated = np.convolve(squared, np.ones(window) / window, mode='same')

    peaks, _ = find_peaks(
        integrated,
        height=np.max(integrated) * 0.30,
        distance=int(0.30 * fs)
    )
    return peaks, integrated


def digitize(image_path, duration_seconds=5.0):
    """
    Full pipeline: image path → heart rate + signal.
    Returns: (r_peaks, signal, heart_rate_bpm)
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    img_clean, _ = remove_grid(img)
    xs, ys, _    = extract_trace(img_clean)

    fs = len(xs) / duration_seconds
    r_peaks, _   = pan_tompkins(ys, fs)

    hr_bpm = None
    if len(r_peaks) >= 2:
        hr_bpm = round(60.0 / np.mean(np.diff(r_peaks) / fs), 1)

    return r_peaks, ys, hr_bpm