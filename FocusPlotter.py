# FocusPlotter.py  — live SDNN plot with baseline + alert flags

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import random
from collections import deque

# -----------------------
# Tunable parameters
# -----------------------
DT = 0.1                    # seconds between frames (interval below must match)
DROP_PCT = 0.20             # alert when SDNN < (1 - DROP_PCT)*baseline (20% drop)
SUSTAIN_SEC = 3.0           # drop must persist this long to alert
SUSTAIN_FRAMES = int(SUSTAIN_SEC / DT)

# Baseline EMA time constant: higher = slower (more stable) baseline
TAU_SEC = 30.0
ALPHA = DT / (TAU_SEC + DT) # EMA smoothing factor

# -----------------------
# Baseline helper
# -----------------------
class BaselineEMA:
    def __init__(self, alpha, init=None):
        self.alpha = alpha
        self.value = init

    def update(self, x):
        x = float(x)
        if self.value is None:
            self.value = x
        else:
            self.value = (1 - self.alpha) * self.value + self.alpha * x
        return self.value

# -----------------------
# Demo SDNN source (replace with real stream)
# Creates a dip between t=8s and t=12s to show alerts
# -----------------------
def synth_sdnn(t):
    base = 50 + 3 * random.uniform(-1, 1)  # ≈50 ms ± noise
    if 8.0 <= t <= 12.0:
        base -= 15 + 3 * random.uniform(0, 1)
    return max(5, base)

# -----------------------
# Figure and artists
# -----------------------
fig, ax = plt.subplots()
ax.set_title("SDNN with Baseline & Alerts")
ax.set_xlabel("Time (s)")
ax.set_ylabel("SDNN (ms)")

x_data, y_sdnn = [], []
y_base = []
alert_x, alert_y = [], []   # where alerts are marked

sdnn_line,   = ax.plot([], [], '-',  label="SDNN")
base_line,   = ax.plot([], [], '--', label="Baseline (EMA)")
alert_marks, = ax.plot([], [], 'r|', ms=12, label="Alerts")  # red tick marks

ax.set_xlim(0, 20)
ax.set_ylim(0, 80)
ax.legend(loc="upper right")

baseline = BaselineEMA(alpha=ALPHA)
below_counter = 0           # consecutive frames below threshold
in_alert = False            # latch to avoid duplicate alerts
window = deque(maxlen=300)  # for gentle autoscaling of y-axis

# -----------------------
# Init function
# -----------------------
def init():
    sdnn_line.set_data([], [])
    base_line.set_data([], [])
    alert_marks.set_data([], [])
    return sdnn_line, base_line, alert_marks

# -----------------------
# Update function (runs each frame)
# -----------------------
def update(frame):
    global below_counter, in_alert

    t = frame * DT

    # ---- DATA SOURCE ----
    sdnn = synth_sdnn(t)      # <-- replace with your real-time SDNN value

    # Baseline update (keep adapting during alerts; change if you prefer)
    b = baseline.update(sdnn)

    # Store data for plotting
    x_data.append(t)
    y_sdnn.append(sdnn)
    y_base.append(b)
    window.append(sdnn)

    # Alert logic: percent drop + sustain
    threshold = (1 - DROP_PCT) * b
    is_below = sdnn < threshold

    if is_below:
        below_counter += 1
    else:
        below_counter = 0
        in_alert = False  # reset once condition clears

    if (below_counter >= SUSTAIN_FRAMES) and (not in_alert):
        in_alert = True
        alert_x.append(t)
        alert_y.append(sdnn)
        print(f"[ALERT] t={t:.1f}s SDNN={sdnn:.1f} < {threshold:.1f} (baseline={b:.1f})")

    # Update artists
    sdnn_line.set_data(x_data, y_sdnn)
    base_line.set_data(x_data, y_base)
    alert_marks.set_data(alert_x, alert_y)

    # Scroll x-axis to show last 20 s
    if t > ax.get_xlim()[1]:
        ax.set_xlim(t - 20, t)

    # Gentle y autoscale
    if window:
        ymin = max(0, min(window) - 5)
        ymax = max(60, max(window) + 10)
        ax.set_ylim(ymin, ymax)

    return sdnn_line, base_line, alert_marks

# -----------------------
# Run animation
# -----------------------
ani = animation.FuncAnimation(
    fig, update, frames=range(1000), init_func=init,
    blit=True, interval=int(DT * 1000), repeat=False
)

plt.show()