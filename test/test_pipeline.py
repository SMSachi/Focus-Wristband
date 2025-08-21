# test/test_pipeline.py
"""
End-to-end pipeline test: RR -> SDNN -> EMA baseline -> alert.
Also logs CSV with RR, SDNN, baseline, threshold, and alert flag.

You can run this file directly:
    python test/test_pipeline.py
It will generate a CSV (pipeline_log.csv) and print alerts to console.
"""

import math
import random
import csv
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np

# --------------------------------------------------------
# Parameters for the pipeline (tweak to experiment)
# --------------------------------------------------------
DT = 0.1                      # "frame" period in seconds (0.1 s = 10 Hz update rate)
TAU_SEC = 30.0                # EMA baseline time constant (bigger = slower baseline drift)
ALPHA = DT / (TAU_SEC + DT)   # smoothing factor for EMA baseline
DROP_PCT = 0.20               # alert when SDNN < (1 - DROP_PCT)*baseline (20% drop)
SUSTAIN_SEC = 3.0             # drop must last this many seconds before triggering
SUSTAIN_FRAMES = int(SUSTAIN_SEC / DT)  # convert sustain duration into number of frames
ROLLING_WINDOW_SEC = 5.0      # compute SDNN over this window of RR intervals
ROLLING_FRAMES = max(3, int(ROLLING_WINDOW_SEC / DT))  # number of samples in SDNN window


# --------------------------------------------------------
# Baseline tracker (EMA)
# --------------------------------------------------------
class BaselineEMA:
    """
    Maintains an exponential moving average (EMA).
    Used here to track a slowly adapting "baseline SDNN".
    """
    def __init__(self, alpha: float, init: float | None = None):
        self.alpha = float(alpha)
        self.value = None if init is None else float(init)

    def update(self, x: float) -> float:
        """
        Update EMA with new value x.
        Formula: new_val = (1-alpha)*old + alpha*x
        """
        x = float(x)
        if self.value is None:
            self.value = x  # initialize on first call
        else:
            self.value = (1 - self.alpha) * self.value + self.alpha * x
        return self.value


# --------------------------------------------------------
# HRV metric: SDNN
# --------------------------------------------------------
def compute_sdnn(rr_ms_window: Iterable[float]) -> float:
    """
    Compute standard deviation of NN intervals (SDNN) from RR window.
    Input: list of RR intervals in ms
    Output: SDNN (ms)
    """
    arr = np.asarray(list(rr_ms_window), dtype=float)
    if arr.size < 2:
        return float("nan")  # not enough data yet
    return float(np.std(arr, ddof=1))  # ddof=1 gives unbiased estimator


# --------------------------------------------------------
# RR interval simulation
# --------------------------------------------------------
@dataclass
class RRPhase:
    """
    Defines one 'phase' of simulated RR intervals.
    - duration_sec: how long this phase lasts
    - mean_ms: average RR interval (e.g., 1000 ms = 60 bpm)
    - sigma_ms: variability (controls SDNN; low sigma = stress)
    """
    duration_sec: float
    mean_ms: float
    sigma_ms: float


def synth_rr_series(phases: List[RRPhase], dt: float, seed: int = 7) -> List[float]:
    """
    Generate a sequence of RR intervals (ms) across phases.
    Each phase produces RR samples with Gaussian noise.
    """
    random.seed(seed)
    rr: List[float] = []
    for ph in phases:
        n = int(ph.duration_sec / dt)  # number of samples in this phase
        for _ in range(n):
            # sample RR around mean with std = sigma
            val = random.gauss(ph.mean_ms, ph.sigma_ms)
            # clamp to reasonable physiological range
            val = max(300.0, min(2000.0, val))
            rr.append(val)
    return rr


# --------------------------------------------------------
# Rolling SDNN
# --------------------------------------------------------
def rolling_sdnn(rr_series: List[float], window_frames: int) -> List[float]:
    """
    Compute SDNN at each time step using a sliding window
    over the last 'window_frames' RR intervals.
    """
    sdnn_series: List[float] = []
    for i in range(len(rr_series)):
        start = max(0, i - window_frames + 1)
        win = rr_series[start : i + 1]
        sdnn_series.append(compute_sdnn(win))
    return sdnn_series


# --------------------------------------------------------
# Alert detection + CSV logging
# --------------------------------------------------------
def detect_alerts_and_log(rr_series: List[float],
                          sdnn_series: List[float],
                          alpha: float,
                          drop_pct: float,
                          sustain_frames: int,
                          csv_path: str) -> List[Tuple[int, float, float, float]]:
    """
    Detect alerts and log pipeline output to CSV.

    CSV columns:
    frame,time_s,RR_ms,SDNN_ms,Baseline_ms,Threshold_ms,AlertFlag

    Returns:
    list of alerts, each entry = (frame_index, sdnn_val, threshold, baseline)
    """
    baseline = BaselineEMA(alpha=alpha)
    below_counter = 0     # counts consecutive frames below threshold
    in_alert = False      # latch to prevent multiple alerts in one dip
    alerts: List[Tuple[int, float, float, float]] = []

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame","time_s","RR_ms","SDNN_ms","Baseline_ms","Threshold_ms","AlertFlag"])

        for i, (rr, sdnn) in enumerate(zip(rr_series, sdnn_series)):
            # skip until SDNN is defined
            if not math.isfinite(sdnn):
                continue

            t = i * DT
            b = baseline.update(sdnn)              # update baseline
            threshold = (1 - drop_pct) * b         # alert threshold

            # check if current SDNN is below threshold
            is_below = sdnn < threshold
            if is_below:
                below_counter += 1
            else:
                below_counter = 0
                in_alert = False

            alert_flag = 0
            if (below_counter >= sustain_frames) and (not in_alert):
                # condition sustained: fire alert
                in_alert = True
                alerts.append((i, sdnn, threshold, b))
                alert_flag = 1

            # log one row to CSV
            writer.writerow([i, f"{t:.2f}", f"{rr:.1f}", f"{sdnn:.2f}",
                             f"{b:.2f}", f"{threshold:.2f}", alert_flag])

    return alerts


# --------------------------------------------------------
# Demo run
# --------------------------------------------------------
def _demo_run():
    print("Running demo and logging CSV...")

    # Define phases: normal -> dip -> recovery
    phases = [
        RRPhase(duration_sec=5.0,  mean_ms=1000.0, sigma_ms=50.0),  # baseline (normal)
        RRPhase(duration_sec=4.0,  mean_ms=1000.0, sigma_ms=15.0),  # sustained dip (stress)
        RRPhase(duration_sec=5.0,  mean_ms=1000.0, sigma_ms=50.0),  # recovery
    ]

    # Generate synthetic RR intervals
    rr = synth_rr_series(phases, dt=DT, seed=123)

    # Compute SDNN time series
    sdnn = rolling_sdnn(rr, window_frames=ROLLING_FRAMES)

    # Run alert detection + log everything to CSV
    alerts = detect_alerts_and_log(rr, sdnn,
                                   alpha=ALPHA,
                                   drop_pct=DROP_PCT,
                                   sustain_frames=SUSTAIN_FRAMES,
                                   csv_path="pipeline_log.csv")

    # Print summary
    print(f"Generated {len(rr)} RR samples. Alerts={len(alerts)}")
    for (i, s, thr, b) in alerts:
        t = i * DT
        print(f"[ALERT] frame={i} t={t:.2f}s SDNN={s:.1f} thr={thr:.1f} baseline={b:.1f}")
    print("CSV written to pipeline_log.csv")


# --------------------------------------------------------
# Entry point
# --------------------------------------------------------
if __name__ == "__main__":
    _demo_run()