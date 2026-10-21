import os
import psutil

flutter_dir = r"C:\Users\hp\OneDrive\Documents\TN_Yield_Model_Phase3_Combined\flutter_app"
chrome_device = os.path.join(flutter_dir, ".dart_tool", "chrome-device")

print("Checking processes holding handles or files in flutter_app...")
found = []
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        cmd = " ".join(p.info['cmdline'] or [])
        if "chrome-device" in cmd or ("flutter" in cmd and "main.dart" in cmd):
            found.append((p.info['pid'], p.info['name'], cmd))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print(f"Found {len(found)} matching processes:")
for pid, name, cmd in found:
    print(f"PID: {pid}, Name: {name}, Cmd: {cmd[:100]}...")
