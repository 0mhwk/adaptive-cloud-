"""
agent/friend_laptop_agent.py
Lightweight Telemetry Agent for Friend's Physical Laptop (Laptop #2, #3, or #4).
Run this script on your friend's laptop to stream their real CPU, RAM,
disk, and Windows processes straight into your AdaptiveCloud Dashboard!

Usage:
    python agent/friend_laptop_agent.py --server http://192.168.1.15:8001 --card 2
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import platform
import socket
import sys
import time
from datetime import datetime, timezone
from typing import Any

# Auto-install psutil if not present
try:
    import psutil
except ImportError:
    print("[INIT] Installing required telemetry module (psutil)...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "requests"])
    import psutil

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
    import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FriendLaptopAgent")


def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


HOSTNAME = socket.gethostname()
LOCAL_IP = get_local_ip()
OS_DETAILS = f"{platform.system()} {platform.release()} ({platform.machine()})"
CPU_CORES = psutil.cpu_count(logical=True) or 4
RAM_TOTAL_GB = round(psutil.virtual_memory().total / (1024 ** 3), 1)

_prev_net = psutil.net_io_counters()
_prev_ts = time.time()


def capture_snapshot(card_id: str) -> dict[str, Any]:
    global _prev_net, _prev_ts
    now_ts = time.time()
    dt = max(0.5, now_ts - _prev_ts)

    cur_net = psutil.net_io_counters()
    net_in_rate = max(0.0, (cur_net.bytes_recv - _prev_net.bytes_recv) / dt)
    net_out_rate = max(0.0, (cur_net.bytes_sent - _prev_net.bytes_sent) / dt)
    _prev_net = cur_net
    _prev_ts = now_ts

    cpu_val = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/")

    try:
        conn_count = len(psutil.net_connections(kind="inet"))
    except Exception:
        conn_count = len(psutil.pids()) // 2

    # Top processes
    top_procs: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
        try:
            pinfo = proc.info
            top_procs.append({
                "pid": pinfo["pid"],
                "name": pinfo["name"] or "process",
                "cpu_percent": round(pinfo["cpu_percent"] or 0.0, 1),
                "memory_mb": round((pinfo["memory_info"].rss if pinfo["memory_info"] else 0) / 1024 / 1024, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    top_procs = sorted(top_procs, key=lambda x: x["cpu_percent"], reverse=True)[:5]

    return {
        "host_id": card_id,
        "hostname": HOSTNAME,
        "display_label": f"Friend's Laptop ({HOSTNAME})",
        "ip_address": LOCAL_IP,
        "os_version": OS_DETAILS,
        "is_physical": True,
        "status": "online",
        "cpu": round(cpu_val, 1),
        "mem": round(mem.percent, 1),
        "disk": round(disk.percent, 1),
        "conn_count": conn_count,
        "top_processes": top_procs,
        "cores": CPU_CORES,
        "ram_gb": RAM_TOTAL_GB,
        "ts": datetime.now(timezone.utc).isoformat(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="AdaptiveCloud Friend Laptop Agent")
    parser.add_argument("--server", type=str, default="", help="Server IP or URL (e.g. http://192.168.1.15:8001)")
    parser.add_argument("--card", type=int, default=2, choices=[2, 3, 4], help="Card slot on dashboard (2, 3, or 4)")
    args = parser.parse_args()

    server_url = args.server.strip()
    if not server_url:
        print("\n" + "=" * 65)
        print("     CONNECT FRIEND'S LAPTOP TO ADAPTIVECLOUD SERVER")
        print("=" * 65)
        server_ip = input("\nEnter the Server Laptop IP (e.g. 192.168.1.15): ").strip()
        if not server_ip.startswith("http"):
            server_url = f"http://{server_ip}:8001"
        else:
            server_url = server_ip

    card_slot = f"host-laptop-0{args.card}"

    banner = f"""
======================================================================
  FRIEND'S PHYSICAL LAPTOP CONNECTED TO ADAPTIVECLOUD
======================================================================
  [+] Friend's Hostname  : {HOSTNAME}
  [+] Operating System   : {OS_DETAILS}
  [+] Local IP Address   : {LOCAL_IP}
  [+] Target Server      : {server_url}
  [+] Assigned Dashboard : PHYSICAL LAPTOP #{args.card} ({card_slot})
======================================================================
Streaming live telemetry every 2 seconds... Press Ctrl+C to stop.
"""
    print(banner)

    # Prime CPU counters
    psutil.cpu_percent(interval=0.5)

    session = requests.Session()
    endpoint = f"{server_url.rstrip('/')}/register-peer"

    fail_count = 0
    while True:
        try:
            snapshot = capture_snapshot(card_slot)
            resp = session.post(endpoint, json=snapshot, timeout=5)
            if resp.ok:
                logger.info(
                    "Sent to Dashboard -> CPU: %4.1f%% | RAM: %4.1f%% | Active Sockets: %2d | Host: %s",
                    snapshot["cpu"], snapshot["mem"], snapshot["conn_count"], HOSTNAME,
                )
                fail_count = 0
            else:
                logger.warning("Server responded with code %d", resp.status_code)
        except Exception as e:
            fail_count += 1
            if fail_count == 1:
                logger.error("Could not reach Server at %s. Ensure both laptops are on same Wi-Fi!", server_url)
            elif fail_count % 5 == 0:
                logger.info("Still attempting to connect to server (%s)...", server_url)

        time.sleep(2.0)


if __name__ == "__main__":
    main()
