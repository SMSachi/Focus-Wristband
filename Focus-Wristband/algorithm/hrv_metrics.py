import numpy as np

def compute_sdnn(rr_intervals_ms):
    """Standard deviation of NN intervals (SDNN)."""
    return np.std(rr_intervals_ms, ddof=1)

def compute_rmssd(rr_intervals_ms):
    """Root mean square of successive differences (RMSSD)."""
    diff_rr = np.diff(rr_intervals_ms)
    return np.sqrt(np.mean(diff_rr**2))
