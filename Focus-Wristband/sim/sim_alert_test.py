import numpy as np
import matplotlib.pyplot as plt
from algorithm.hrv_metrics import compute_sdnn
from baseline import BaselineEMA

# Simulate RR intervals with a dip in variability
def generate_rr_stream():
    np.random.seed(0)
    normal = np.random.normal(800, 50, size=100)        # Normal HRV
    dip = np.random.normal(800, 10, size=40)            # Low HRV
    recover = np.random.normal(800, 50, size=60)        # Recovery
    return np.concatenate([normal, dip, recover])

rr_stream = generate_rr_stream()
window_size = 30  # rolling window to compute SDNN
baseline = BaselineEMA(alpha=0.05)
sdnn_list = []
baseline_list = []
alert_indices = []

for i in range(len(rr_stream) - window_size):
    window = rr_stream[i:i+window_size]
    sdnn = compute_sdnn(window)
    baseline_val = baseline.update(sdnn)

    sdnn_list.append(sdnn)
    baseline_list.append(baseline_val)

    if sdnn < 0.8 * baseline_val:  # Trigger alert if SDNN drops 20% below baseline
        alert_indices.append(i + window_size)

# Plot
plt.plot(sdnn_list, label='SDNN')
plt.plot(baseline_list, label='Baseline EMA', linestyle='--')
plt.scatter(alert_indices, [sdnn_list[i - window_size] for i in alert_indices], color='red', label='Alert')
plt.title("SDNN vs Baseline with Alerts")
plt.xlabel("Time Index")
plt.ylabel("SDNN (ms)")
plt.legend()
plt.show()

