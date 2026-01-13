# Focus Wristband (Laptop BLE Edition)

A self-built wearable that measures heart rate (HR), heart rate variability (HRV), and SpO₂ using the MAX30102 sensor and streams data over Bluetooth Low Energy (BLE) to a Python dashboard running on your laptop. When your HRV drops below baseline for 30+ seconds (indicating rising stress), it triggers a gentle vibration alert.

---

## 📦 Project Features

| Feature               | Description                                                            |
|-----------------------|------------------------------------------------------------------------|
| ✅ Real-time HR + HRV | Rolling HR and SDNN from optical PPG (MAX30102)                        |
| ✅ BLE streaming      | ESP32-S3 sends data to laptop via Bluetooth                            |
| ✅ Python dashboard   | Logs HR/HRV, saves CSV, and shows real-time Matplotlib charts          |
| ✅ Alert system       | Haptic alert when HRV < 80% of baseline for 30 seconds                 |
| 🚫 No mobile app      | Fully laptop-run; no smartphone or backend required                    |

---

## 🧠 System Architecture

        [MAX30102 Sensor]
               │
        (I²C: SDA/SCL)
               ↓
       [ESP32-S3 Feather]
               │
  ┌──────────────────────────────┐
  │  HR & HRV Calc (SDNN)        │
  │  Baseline Tracking (EMA)     │
  │  BLE Advertiser (HR/HRV)     │
  └──────────────────────────────┘
               │
       Bluetooth Low Energy
               ↓
      [Laptop Python Script]
               │
       ┌────────────────────┐
       │   FocusPlotter.py  │
       │  • BLE receiver    │
       │  • CSV logger      │
       │  • Live plots      │
       └────────────────────┘


---

## 🧰 Hardware List

| Component                        | Purpose                     | Est. Cost |
|----------------------------------|-----------------------------|-----------|
| Adafruit ESP32-S3 Feather        | MCU + BLE + Li-Po charging | ~$17      |
| MAX30102 sensor module           | PPG sensor (HR/SpO₂)       | ~$7       |
| 500 mAh Li-Po battery (JST)      | Power supply                | ~$7       |
| Coin vibration motor + NPN/diode | Haptic alert                | ~$4       |
| Velcro wrist strap               | Wearable form factor        | ~$7       |
| 3D-printed case (optional)       | Clean enclosure             | ~$1       |

---

## 🗂 Repo Structure

| Path / File         | Role                                                       |
|---------------------|------------------------------------------------------------|
| `algorithm/`        | Signal processing: HR, SDNN, etc.                          |
| `sim/`              | Simulation tools (e.g., test data, fake packet generator) |
| `test/`             | Unit tests                                                 |
| `utils/`            | Helper scripts (e.g., BLE formatting, data I/O)           |
| `baseline.py`       | Exponential moving average (EMA) baseline tracker         |
| `main_logic.py`     | Core logic: alerting, HRV comparison, data packaging      |
| `FocusPlotter.py`   | BLE dashboard: data receive, CSV log, live plot           |
| `README.md`         | Project overview (you’re reading it!)                     |

---

## 📈 How to Run (BLE Logger)

1. **Install dependencies**
   ```bash
   pip install bleak pandas matplotlib
2. **Start the script
**
python FocusPlotter.py

3. **View**

A real-time Matplotlib window with HR and HRV

A .csv log saved with timestamped data

Note: the ESP32-S3 must be powered on and advertising BLE packets with characteristics for HR, HRV, SpO₂.
