"""
agent/run_laptop_agent.py
Central Physical Laptop Telemetry Hub for AdaptiveCloud.
Runs on your host laptop (port 8001).
Collects your local hardware metrics AND acts as the receiver
for your friends' physical laptops (Laptop #2, #3, #4) across the Wi-Fi network!

Usage:
    python agent/run_laptop_agent.py
"""

from __future__ import annotations

import collections
import json
import logging
import os
import platform
import socket
import sys
import threading
import time
import urllib.parse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.incident_store import incident_store
from core.rca_engine import rca_engine
from core.tier_classifiers import tier_classifiers

# Ensure psutil is installed
try:
    import psutil
except ImportError:
    print("[AGENT INIT] psutil not detected. Installing psutil automatically...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

# Configuration
PORT = int(os.environ.get("AGENT_PORT", "8001"))
HOST = "0.0.0.0"
HISTORY_LEN = 30
SAMPLE_INTERVAL_SEC = 2.0

# Setup Console Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("AdaptiveHubAgent")

# Rolling Telemetry Buffer for Host Laptop (Card #1)
telemetry_history: collections.deque[dict[str, Any]] = collections.deque(maxlen=HISTORY_LEN)
telemetry_lock = threading.Lock()

# Peer Friend Laptops Storage (Cards #2, #3, #4)
peer_laptops: dict[str, dict[str, Any]] = {}
peer_histories: dict[str, collections.deque[dict[str, Any]]] = collections.defaultdict(
    lambda: collections.deque(maxlen=HISTORY_LEN)
)
peer_lock = threading.Lock()


def get_local_ip() -> str:
    """Detect the active local LAN/WiFi IP of this laptop."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


# Hardware Metadata
HOSTNAME = socket.gethostname()
LOCAL_IP = get_local_ip()
OS_DETAILS = f"{platform.system()} {platform.release()} ({platform.machine()})"
CPU_CORES = psutil.cpu_count(logical=True) or 4
RAM_TOTAL_GB = round(psutil.virtual_memory().total / (1024 ** 3), 1)

# Initialize network / disk counters
_prev_net = psutil.net_io_counters()
_prev_ts = time.time()


def sample_metrics() -> dict[str, Any]:
    """Capture real-time physical telemetry snapshot from this machine."""
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

    # Sockets / active connections
    try:
        conn_count = len(psutil.net_connections(kind="inet"))
    except Exception:
        conn_count = len(psutil.pids()) // 2

    # Top processes by CPU
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

    top_procs = sorted(top_procs, key=lambda x: x["cpu_percent"], reverse=True)[:6]

    return {
        "id": f"metric-live-{int(now_ts * 1000)}",
        "host_id": "host-laptop-01",
        "ts": datetime.now(timezone.utc).isoformat(),
        "cpu": round(cpu_val, 1),
        "mem": round(mem.percent, 1),
        "disk": round(disk.percent, 1),
        "net_in": round(net_in_rate / 1024, 1),
        "net_out": round(net_out_rate / 1024, 1),
        "load": round(cpu_val / 25.0, 2),
        "proc_count": len(psutil.pids()),
        "conn_count": conn_count,
        "extra": {
            "top_cpu_processes": top_procs,
            "host_info": {
                "hostname": HOSTNAME,
                "ip": LOCAL_IP,
                "os": OS_DETAILS,
                "cores": CPU_CORES,
                "ram_gb": RAM_TOTAL_GB,
            },
        },
    }


def collector_loop() -> None:
    """Background thread that populates telemetry buffer continuously."""
    psutil.cpu_percent(interval=0.5)

    for i in range(10):
        snap = sample_metrics()
        telemetry_history.append(snap)
        time.sleep(0.1)

    while True:
        try:
            snapshot = sample_metrics()
            with telemetry_lock:
                telemetry_history.append(snapshot)
            logger.info(
                "Host Telemetry (Card #1) -> CPU: %4.1f%% | RAM: %4.1f%% | Active Procs: %3d | Connected Peers: %d",
                snapshot["cpu"], snapshot["mem"], snapshot["proc_count"], len(peer_laptops),
            )
        except Exception as e:
            logger.error("Collector exception: %s", e)
        time.sleep(SAMPLE_INTERVAL_SEC)


class AgentRequestHandler(BaseHTTPRequestHandler):
    """CORS-enabled HTTP Request Handler for Dashboard & Friend Peer Laptops."""

    def _set_cors_headers(self, content_type: str = "application/json") -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self) -> None:
        self._set_cors_headers()

    def do_POST(self) -> None:
        clean_path = self.path.split("?")[0]

        # Ingestion endpoint for friend laptops
        if clean_path in ("/register-peer", "/ingest-peer"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                card_id = payload.get("host_id", "host-laptop-02")
                with peer_lock:
                    peer_laptops[card_id] = payload
                    peer_histories[card_id].append({
                        "id": f"metric-peer-{int(time.time() * 1000)}",
                        "host_id": card_id,
                        "ts": payload.get("ts", datetime.now(timezone.utc).isoformat()),
                        "cpu": payload.get("cpu", 30),
                        "mem": payload.get("mem", 50),
                        "disk": payload.get("disk", 50),
                        "conn_count": payload.get("conn_count", 25),
                        "extra": {
                            "top_cpu_processes": payload.get("top_processes", []),
                        },
                    })
                logger.info(
                    "[+] PEER UPDATE -> %s (%s) | CPU: %s%% | RAM: %s%%",
                    card_id, payload.get("hostname", "Unknown"), payload.get("cpu"), payload.get("mem")
                )
                self._set_cors_headers()
                self.wfile.write(b'{"status": "ok", "message": "Peer telemetry received"}')
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Permission Gate: POST /incidents/{id}/approve
        if "/approve" in clean_path:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
            parts = clean_path.strip("/").split("/")
            inc_id = parts[1] if len(parts) >= 3 else parts[0]
            try:
                updated = incident_store.approve_and_execute(
                    incident_id=inc_id,
                    action_ids=body.get("action_ids"),
                    decided_by=body.get("decided_by", "Operator"),
                    comment=body.get("comment", ""),
                    dry_run=body.get("dry_run", True),
                )
                self._set_cors_headers()
                self.wfile.write(json.dumps(updated).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        # Permission Gate: POST /incidents/{id}/reject
        if "/reject" in clean_path:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
            parts = clean_path.strip("/").split("/")
            inc_id = parts[1] if len(parts) >= 3 else parts[0]
            try:
                updated = incident_store.reject_action(
                    incident_id=inc_id,
                    decided_by=body.get("decided_by", "Operator"),
                    comment=body.get("comment", ""),
                )
                self._set_cors_headers()
                self.wfile.write(json.dumps(updated).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        # Rollback: POST /incidents/{id}/rollback
        if "/rollback" in clean_path:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
            parts = clean_path.strip("/").split("/")
            inc_id = parts[1] if len(parts) >= 3 else parts[0]
            try:
                updated = incident_store.rollback_action(
                    incident_id=inc_id,
                    decided_by=body.get("decided_by", "Operator"),
                    comment=body.get("comment", ""),
                    dry_run=body.get("dry_run", True),
                )
                self._set_cors_headers()
                self.wfile.write(json.dumps(updated).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        self.send_response(404)
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        clean_path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # Incident Store & Permission Gate: GET /incidents
        if clean_path in ("/incidents", "/api/v1/incidents"):
            self._set_cors_headers()
            incident_store.check_expirations(timeout_seconds=300)
            family = query_params.get("family", [None])[0]
            status_param = query_params.get("status", [None])[0]
            source = query_params.get("source", [None])[0]
            limit_param = int(query_params.get("limit", ["100"])[0])

            items = incident_store.list_incidents(
                family=family,
                status=status_param,
                source=source,
                limit=limit_param,
            )
            self.wfile.write(json.dumps(items).encode("utf-8"))
            return

        # GET /incidents/{id}
        if clean_path.startswith("/incidents/") or clean_path.startswith("/api/v1/incidents/"):
            parts = clean_path.strip("/").split("/")
            inc_id = parts[-1]
            inc = incident_store.get_incident(inc_id)
            if inc:
                self._set_cors_headers()
                self.wfile.write(json.dumps(inc).encode("utf-8"))
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Incident {inc_id} not found"}).encode("utf-8"))
            return

        if clean_path in ("/", "/info", "/status"):
            self._set_cors_headers()
            payload = {
                "status": "online",
                "agent_version": "2.5.0-hub",
                "hostname": HOSTNAME,
                "ip_address": LOCAL_IP,
                "os_version": OS_DETAILS,
                "agent_platform": "windows" if os.name == "nt" else "linux",
                "cores": CPU_CORES,
                "ram_total_gb": RAM_TOTAL_GB,
                "is_physical": True,
                "peer_laptops_count": len(peer_laptops),
            }
            self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))
            return

        # List all connected friend laptops
        if clean_path in ("/peers", "/peer-laptops"):
            self._set_cors_headers()
            with peer_lock:
                self.wfile.write(json.dumps(peer_laptops).encode("utf-8"))
            return

        # Host Laptop (Card #1) Telemetry
        if clean_path in ("/telemetry", "/metrics", "/hosts/host-laptop-01/metrics"):
            self._set_cors_headers()
            with telemetry_lock:
                points_list = list(telemetry_history)
            latest = points_list[-1] if points_list else {}
            payload = {
                "host_id": "host-laptop-01",
                "status": "online",
                "hostname": HOSTNAME,
                "ip_address": LOCAL_IP,
                "os_version": OS_DETAILS,
                "is_physical": True,
                "points": points_list,
                "latest": latest,
            }
            self.wfile.write(json.dumps(payload).encode("utf-8"))
            return

        # Friend Peer Laptops (Cards #2, #3, #4) Telemetry
        for card_id in ["host-laptop-02", "host-laptop-03", "host-laptop-04"]:
            if clean_path in (f"/hosts/{card_id}/metrics", f"/{card_id}/telemetry"):
                self._set_cors_headers()
                with peer_lock:
                    if card_id in peer_histories and len(peer_histories[card_id]) > 0:
                        points_list = list(peer_histories[card_id])
                        peer_meta = peer_laptops.get(card_id, {})
                        payload = {
                            "host_id": card_id,
                            "status": "online",
                            "hostname": peer_meta.get("hostname", f"Physical-Laptop-{card_id[-1]}"),
                            "ip_address": peer_meta.get("ip_address", "192.168.1.10x"),
                            "os_version": peer_meta.get("os_version", "Windows Physical"),
                            "is_physical": True,
                            "points": points_list,
                            "latest": points_list[-1],
                        }
                        self.wfile.write(json.dumps(payload).encode("utf-8"))
                        return

        # 404 handler
        self.send_response(404)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"error": "Endpoint not found"}')

    def log_message(self, format: str, *args: Any) -> None:
        pass


def main() -> None:
    banner = f"""
======================================================================
      ADAPTIVECLOUD PHYSICAL HUB & PEER AGENT v2.5.0
======================================================================
  [+] Host Machine Name : {HOSTNAME}
  [+] Host OS           : {OS_DETAILS}
  [+] Local Wi-Fi IP    : {LOCAL_IP}
  [+] Hub Port          : {PORT}
  [+] Peer Ingest URL   : http://{LOCAL_IP}:{PORT}/register-peer
----------------------------------------------------------------------
  HOW TO CONNECT YOUR FRIEND'S LAPTOP TO THIS SERVER:
  1. Make sure your friend is connected to the SAME Wi-Fi network.
  2. On your friend's laptop, run:
     python agent/friend_laptop_agent.py --server http://{LOCAL_IP}:{PORT} --card 2
======================================================================
    """
    print(banner)

    collector_thread = threading.Thread(target=collector_loop, daemon=True)
    collector_thread.start()

    server = HTTPServer((HOST, PORT), AgentRequestHandler)
    logger.info("AdaptiveCloud Hub listening on port %d...", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nHub agent gracefully shutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
