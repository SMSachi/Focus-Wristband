import asyncio
import datetime
import csv
from bleak import BleakClient, BleakScanner
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ======== SET THESE VALUES ========
TARGET_NAME = "FocusBand"  # Your phone or ESP32 name in nRF Connect
CHAR_UUID_HR = "00002a37-0000-1000-8000-00805f9b34fb"    # Heart Rate
CHAR_UUID_HRV = "2d30-0001-0000-1000-00805f9b34fb"       # HRV (custom)
CHAR_UUID_SPO2 = "2d30-0002-0000-1000-00805f9b34fb"      # SpO₂ (custom)
# ===================================

# Data buffers
timestamps, hr_data, hrv_data = [], [], []

# CSV logging
filename = f"focusband_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_file = open(filename, mode='w', newline='')
csv_writer = csv.writer(csv_file)
csv_writer.writerow(['Time', 'HR', 'HRV'])

# BLE notification handler
def handle_notify(uuid, data):
    global timestamps, hr_data, hrv_data

    time_now = datetime.datetime.now().strftime('%H:%M:%S')

    if uuid == CHAR_UUID_HR:
        hr = int.from_bytes(data, byteorder='little')
        hr_data.append(hr)
        print(f"[{time_now}] ❤️ HR: {hr}")
    elif uuid == CHAR_UUID_HRV:
        hrv = int.from_bytes(data, byteorder='little')
        hrv_data.append(hrv)
        print(f"[{time_now}] 🔄 HRV: {hrv}")
    elif uuid == CHAR_UUID_SPO2:
        spo2 = int.from_bytes(data, byteorder='little')
        print(f"[{time_now}] 🫁 SpO2: {spo2}")
    else:
        return

    # Log to CSV
    last_hr = hr_data[-1] if hr_data else ''
    last_hrv = hrv_data[-1] if hrv_data else ''
    csv_writer.writerow([time_now, last_hr, last_hrv])

# Plotting setup
plt.style.use('seaborn-darkgrid')
fig, ax = plt.subplots()
line_hr, = ax.plot([], [], label='HR (bpm)', color='red')
line_hrv, = ax.plot([], [], label='HRV (ms)', color='blue')

def update(frame):
    if not timestamps:
        return line_hr, line_hrv
    t = list(range(len(hr_data)))
    line_hr.set_data(t, hr_data)
    line_hrv.set_data(t, hrv_data)
    ax.relim()
    ax.autoscale_view()
    return line_hr, line_hrv

async def main():
    print("🔍 Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    target = None
    for d in devices:
        if d.name == TARGET_NAME:
            target = d
            break

    if not target:
        print(f"❌ Could not find device: {TARGET_NAME}")
        return

    print(f"✅ Found {target.name} at {target.address}")
    async with BleakClient(target.address) as client:
        print("📡 Connected. Subscribing to notifications...")

        await client.start_notify(CHAR_UUID_HR, handle_notify)
        await client.start_notify(CHAR_UUID_HRV, handle_notify)
        await client.start_notify(CHAR_UUID_SPO2, handle_notify)

        ani = FuncAnimation(fig, update, interval=1000)
        plt.legend()
        plt.title("Focus Wristband Live Data")
        plt.xlabel("Time (s)")
        plt.ylabel("Values")
        plt.tight_layout()
        plt.show()

        await client.stop_notify(CHAR_UUID_HR)
        await client.stop_notify(CHAR_UUID_HRV)
        await client.stop_notify(CHAR_UUID_SPO2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
    finally:
        csv_file.close()
