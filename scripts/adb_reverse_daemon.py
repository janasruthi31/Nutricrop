import subprocess
import time
import sys

def main():
    device = "DMT4DYYLIN8XIRV8"
    cmd = ["adb", "-s", device, "reverse", "tcp:8000", "tcp:8000"]
    print(f"Setting up ADB reverse port forward: {' '.join(cmd)}", flush=True)
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Output: {res.stdout.strip()} {res.stderr.strip()}", flush=True)
    
    list_cmd = ["adb", "-s", device, "reverse", "--list"]
    res_list = subprocess.run(list_cmd, capture_output=True, text=True)
    print(f"Active reverse forwards:\n{res_list.stdout.strip()}", flush=True)

    while True:
        time.sleep(5)
        res_list = subprocess.run(list_cmd, capture_output=True, text=True)
        if "tcp:8000" not in res_list.stdout:
            print("Port forward lost, re-establishing...", flush=True)
            subprocess.run(cmd, capture_output=True, text=True)

if __name__ == "__main__":
    main()
