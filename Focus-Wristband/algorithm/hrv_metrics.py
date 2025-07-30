import numpy as np
import neurokit2 as nk

def compute_hrv_metrics(ppg_signal, sampling_rate=100):
    # Clean the PPG signal
    cleaned = nk.ppg_clean(ppg_signal, sampling_rate=sampling_rate)

    # Extract peaks (heartbeats)
    peaks, _ = nk.ppg_peaks(cleaned, sampling_rate=sampling_rate)
    peak_times = np.where(peaks["PPG_Peaks"] == 1)[0] / sampling_rate  # in seconds

    # Compute HRV metrics from peak times
    hrv = nk.hrv_time(peak_times, sampling_rate=sampling_rate, show=False)

    return hrv[["HRV_SDNN", "HRV_RMSSD"]].iloc[0].to_dict()
