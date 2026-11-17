"""
agent/simulate_all_laptops.py
Multi-Laptop Simulator & Telemetry Hub for AdaptiveCloud.
Runs on your single laptop and makes ALL 4 PHYSICAL LAPTOPS LIVE!
- Laptop #1: Streams your actual physical hardware CPU, RAM, and processes.
- Laptop #2, #3, #4: Stream live simulated physical laptop telemetry.

Usage:
    python agent/simulate_all_laptops.py
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

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.incident_store import incident_store
from core.rca_engine import rca_engine
from core.tier_classifiers import tier_classifiers

try:
    import psutil
except ImportError:
    print("[INIT] Installing psutil...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
    import psutil

PORT = int(os.environ.get("AGENT_PORT", "8001"))
HOST = "0.0.0.0"
HISTORY_LEN = 30

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MultiLaptopSimulator")

# Storage for all physical & AWS cloud nodes
fleet_history: dict[str, collections.deque[dict[str, Any]]] = {
    "host-laptop-01": collections.deque(maxlen=HISTORY_LEN),
    "host-laptop-02": collections.deque(maxlen=HISTORY_LEN),
    "host-laptop-03": collections.deque(maxlen=HISTORY_LEN),
    "host-laptop-04": collections.deque(maxlen=HISTORY_LEN),
    "aws-worker-01": collections.deque(maxlen=HISTORY_LEN),
    "aws-worker-02": collections.deque(maxlen=HISTORY_LEN),
    "aws-gateway-01": collections.deque(maxlen=HISTORY_LEN),
    "aws-db-01": collections.deque(maxlen=HISTORY_LEN),
}
fleet_lock = threading.Lock()

# Dynamic live anomalies container for demonstration
active_anomalies: dict[str, dict[str, Any]] = {}

# Registered AWS EC2 Cloud Fleet (ap-south-1 Mumbai)
registered_aws_workers: list[dict[str, Any]] = [
    {
        "id": "aws-worker-01",
        "instance_id": "i-017c3c1add524779c",
        "name": "AdaptiveCloud-Worker-01",
        "display_label": "AWS EC2 Worker 01 (i-017c3c1add524779c)",
        "type": "t2.micro (Free Tier)",
        "state": "running",
        "ip_address": "3.108.250.115",
        "public_ip": "3.108.250.115",
        "private_ip": "172.31.6.242",
        "region": "ap-south-1b (Mumbai)",
        "os_version": "Amazon Linux 2023 (ap-south-1b)",
        "agent_platform": "linux",
        "status": "online",
        "is_cloud": True,
        "is_physical": False,
        "cpu": 18.2,
        "mem": 44.5,
        "disk": 22.8,
        "launch_time": "2026-11-17T09:27:00Z",
    },
    {
        "id": "aws-worker-02",
        "instance_id": "i-0ab2c3d4e5f678901",
        "name": "AdaptiveCloud-Worker-02",
        "display_label": "AWS EC2 Worker 02 (ap-south-1a)",
        "type": "t2.micro (Free Tier)",
        "state": "running",
        "ip_address": "13.233.142.76",
        "public_ip": "13.233.142.76",
        "private_ip": "172.31.18.94",
        "region": "ap-south-1a (Mumbai)",
        "os_version": "Amazon Linux 2023 (ap-south-1a)",
        "agent_platform": "linux",
        "status": "online",
        "is_cloud": True,
        "is_physical": False,
        "cpu": 14.5,
        "mem": 38.2,
        "disk": 19.5,
        "launch_time": "2026-11-17T11:15:00Z",
    },
    {
        "id": "aws-gateway-01",
        "instance_id": "i-09f1a238e5b4c10aa",
        "name": "AWS-Ingress-Gateway-01",
        "display_label": "AWS Cloud Ingress Gateway (i-09f1a238e5b4c10aa)",
        "type": "t3.medium (WAF Edge)",
        "state": "running",
        "ip_address": "13.127.88.204",
        "public_ip": "13.127.88.204",
        "private_ip": "172.31.10.5",
        "region": "ap-south-1b (Mumbai)",
        "os_version": "Amazon Linux 2023 (ALB Edge)",
        "agent_platform": "linux",
        "status": "online",
        "is_cloud": True,
        "is_physical": False,
        "cpu": 22.0,
        "mem": 48.0,
        "disk": 24.5,
        "launch_time": "2026-11-17T08:00:00Z",
    },
    {
        "id": "aws-db-01",
        "instance_id": "i-0bb8214f9d0c24e12",
        "name": "AWS-Database-Primary",
        "display_label": "AWS RDS Database Primary (i-0bb8214f9d0c24e12)",
        "type": "m5.large (EBS Volume)",
        "state": "running",
        "ip_address": "13.235.19.44",
        "public_ip": "13.235.19.44",
        "private_ip": "172.31.28.11",
        "region": "ap-south-1a (Mumbai)",
        "os_version": "Amazon Linux 2023 (PostgreSQL)",
        "agent_platform": "linux",
        "status": "online",
        "is_cloud": True,
        "is_physical": False,
        "cpu": 28.5,
        "mem": 62.0,
        "disk": 44.0,
        "launch_time": "2026-11-17T07:30:00Z",
    },
]

HOSTNAME = socket.gethostname()
LOCAL_IP = "127.0.0.1"
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    LOCAL_IP = s.getsockname()[0]
    s.close()
except Exception:
    pass

OS_DETAILS = f"{platform.system()} {platform.release()} ({platform.machine()})"
CPU_CORES = psutil.cpu_count(logical=True) or 4
RAM_TOTAL_GB = round(psutil.virtual_memory().total / (1024 ** 3), 1)


def generate_fleet_snapshots() -> None:
    """Collect real telemetry for Laptop 1, and simulated hardware telemetry for Laptops 2-4."""
    now_ts = time.time()
    iso_ts = datetime.now(timezone.utc).isoformat()

    # LAPTOP 1: Real Local Hardware
    real_cpu = psutil.cpu_percent(interval=None)
    real_mem = psutil.virtual_memory().percent
    real_disk = psutil.disk_usage("C:\\" if os.name == "nt" else "/").percent
    try:
        real_conns = len(psutil.net_connections(kind="inet"))
    except Exception:
        real_conns = len(psutil.pids()) // 2

    real_procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent"]):
        try:
            pinfo = proc.info
            real_procs.append({
                "pid": pinfo["pid"],
                "name": pinfo["name"] or "process",
                "cpu_percent": round(pinfo["cpu_percent"] or 0.0, 1),
            })
        except Exception:
            pass
    real_procs = sorted(real_procs, key=lambda x: x["cpu_percent"], reverse=True)[:5]

    snap_1 = {
        "id": f"m-1-{int(now_ts * 1000)}",
        "host_id": "host-laptop-01",
        "ts": iso_ts,
        "cpu": round(real_cpu, 1),
        "mem": round(real_mem, 1),
        "disk": round(real_disk, 1),
        "conn_count": real_conns,
        "load": round(real_cpu / 25.0, 2),
        "extra": {"top_cpu_processes": real_procs},
    }

    # LAPTOP 2: Lab Workstation A (Port Scan activity)
    t = now_ts / 4
    snap_2 = {
        "id": f"m-2-{int(now_ts * 1000)}",
        "host_id": "host-laptop-02",
        "ts": iso_ts,
        "cpu": round(58.0 + 8.0 * ((t % 3) - 1.5), 1),
        "mem": 72.4,
        "disk": 61.2,
        "conn_count": 182,
        "load": 2.1,
        "extra": {
            "top_cpu_processes": [
                {"name": "nmap_probe.exe", "pid": 8840, "cpu_percent": 24.2},
                {"name": "svchost.exe", "pid": 1044, "cpu_percent": 12.8},
                {"name": "chrome.exe", "pid": 6320, "cpu_percent": 6.4},
            ]
        },
    }

    # LAPTOP 3: Dev Workstation B (XMRig Cryptominer)
    snap_3 = {
        "id": f"m-3-{int(now_ts * 1000)}",
        "host_id": "host-laptop-03",
        "ts": iso_ts,
        "cpu": round(92.0 + 3.0 * ((t % 2) - 1.0), 1),
        "mem": 86.5,
        "disk": 48.0,
        "conn_count": 42,
        "load": 3.8,
        "extra": {
            "top_cpu_processes": [
                {"name": "xmrig-daemon", "pid": 4912, "cpu_percent": 68.5},
                {"name": "stratum-worker", "pid": 4913, "cpu_percent": 14.2},
                {"name": "containerd", "pid": 890, "cpu_percent": 4.5},
            ]
        },
    }

    # LAPTOP 4: Field Workstation C (LSASS Dump)
    snap_4 = {
        "id": f"m-4-{int(now_ts * 1000)}",
        "host_id": "host-laptop-04",
        "ts": iso_ts,
        "cpu": round(42.0 + 5.0 * ((t % 4) - 2.0), 1),
        "mem": 68.2,
        "disk": 55.4,
        "conn_count": 28,
        "load": 1.4,
        "extra": {
            "top_cpu_processes": [
                {"name": "lsass.exe (Audit)", "pid": 680, "cpu_percent": 18.2},
                {"name": "mimikatz_probe.exe", "pid": 7420, "cpu_percent": 9.4},
                {"name": "powershell.exe", "pid": 3204, "cpu_percent": 6.8},
            ]
        },
    }

    # AWS WORKER: AdaptiveCloud-Worker-01 (i-017c3c1add524779c)
    snap_aws = {
        "id": f"m-aws-{int(now_ts * 1000)}",
        "host_id": "aws-worker-01",
        "ts": iso_ts,
        "cpu": round(18.0 + 3.0 * ((t % 5) - 2.0), 1),
        "mem": 44.5,
        "disk": 22.8,
        "conn_count": 14,
        "load": 0.35,
        "extra": {
            "top_cpu_processes": [
                {"name": "python3 (agent)", "pid": 1102, "cpu_percent": 1.2},
                {"name": "systemd", "pid": 1, "cpu_percent": 0.4},
                {"name": "sshd", "pid": 890, "cpu_percent": 0.2},
            ]
        },
    }

    # AWS WORKER 2: ap-south-1a (Mumbai) — Healthy secondary worker
    snap_aws2 = {
        "id": f"m-aws2-{int(now_ts * 1000)}",
        "host_id": "aws-worker-02",
        "ts": iso_ts,
        "cpu": round(14.0 + 2.0 * ((t % 7) - 3.5), 1),
        "mem": 38.2,
        "disk": 19.5,
        "conn_count": 8,
        "load": 0.22,
        "extra": {
            "top_cpu_processes": [
                {"name": "nginx", "pid": 1201, "cpu_percent": 0.8},
                {"name": "systemd", "pid": 1, "cpu_percent": 0.3},
            ]
        },
    }

    # AWS Ingress Gateway (WAF / Edge ALB)
    snap_gw = {
        "id": f"m-gw-{int(now_ts * 1000)}",
        "host_id": "aws-gateway-01",
        "ts": iso_ts,
        "cpu": round(22.0 + 3.0 * ((t % 6) - 3.0), 1),
        "mem": 48.0,
        "disk": 24.5,
        "conn_count": 85,
        "load": 0.45,
        "extra": {
            "top_cpu_processes": [
                {"name": "envoy-proxy", "pid": 1050, "cpu_percent": 12.4},
                {"name": "waf_rate_filter", "pid": 1051, "cpu_percent": 6.8},
                {"name": "systemd", "pid": 1, "cpu_percent": 0.4},
            ]
        },
    }

    # AWS RDS Primary Database Cluster
    snap_db = {
        "id": f"m-db-{int(now_ts * 1000)}",
        "host_id": "aws-db-01",
        "ts": iso_ts,
        "cpu": round(28.0 + 4.0 * ((t % 5) - 2.5), 1),
        "mem": 62.0,
        "disk": 44.0,
        "conn_count": 64,
        "load": 0.85,
        "extra": {
            "top_cpu_processes": [
                {"name": "postgres: writer", "pid": 2104, "cpu_percent": 14.5},
                {"name": "postgres: walwriter", "pid": 2105, "cpu_percent": 8.2},
                {"name": "ebs_sync_daemon", "pid": 2110, "cpu_percent": 3.1},
            ]
        },
    }

    all_snaps = {
        "host-laptop-01": snap_1,
        "host-laptop-02": snap_2,
        "host-laptop-03": snap_3,
        "host-laptop-04": snap_4,
        "aws-worker-01": snap_aws,
        "aws-worker-02": snap_aws2,
        "aws-gateway-01": snap_gw,
        "aws-db-01": snap_db,
    }

    # Universally apply any active anomalies to ANY target host
    for hid, snap in all_snaps.items():
        if hid in active_anomalies:
            anom = active_anomalies[hid]
            snap["cpu"] = anom.get("cpu", 93.5)
            snap["mem"] = anom.get("mem", 79.2)
            snap["conn_count"] = anom.get("conn_count", 480)
            snap["load"] = 4.8
            snap["extra"] = {
                "top_cpu_processes": anom.get("processes", [
                    {"name": f"{anom.get('type', 'threat')}_payload", "pid": 9811, "cpu_percent": 84.5},
                    {"name": "python3 (agent)", "pid": 1102, "cpu_percent": 6.8},
                ])
            }

    with fleet_lock:
        for hid, snap in all_snaps.items():
            if hid not in fleet_history:
                fleet_history[hid] = collections.deque(maxlen=HISTORY_LEN)
            fleet_history[hid].append(snap)


def sync_live_aws_instances() -> None:
    """Dynamically poll AWS to discover all live EC2 instances via Boto3."""
    try:
        from scripts.aws_cloud_monitor import list_ec2_instances
        live_list = list_ec2_instances()
        for inst in live_list:
            if inst.get("is_live_aws"):
                inst_id = inst.get("instance_id")
                pub_ip = inst.get("public_ip") or "N/A"
                priv_ip = inst.get("private_ip") or "N/A"
                state = inst.get("state", "running")
                name_tag = inst.get("name") or inst_id
                display = f"{name_tag.split('(')[0].strip()} ({inst_id})" if name_tag else f"AWS EC2 ({inst_id})"

                match = next((w for w in registered_aws_workers if w["id"] == f"aws-{inst_id}" or w.get("instance_id") == inst_id), None)
                if match:
                    match["public_ip"] = pub_ip
                    match["ip_address"] = pub_ip
                    match["private_ip"] = priv_ip
                    match["state"] = state
                    match["status"] = "online" if state == "running" else "offline"
                    if "AdaptiveCloud-Worker" in name_tag:
                        match["display_label"] = display
                else:
                    new_id = f"aws-{inst_id}"
                    registered_aws_workers.append({
                        "id": new_id,
                        "instance_id": inst_id,
                        "name": name_tag,
                        "display_label": display,
                        "type": inst.get("type", "t2.micro"),
                        "state": state,
                        "ip_address": pub_ip,
                        "public_ip": pub_ip,
                        "private_ip": priv_ip,
                        "region": "ap-south-1 (Mumbai)",
                        "os_version": "Amazon Linux 2023",
                        "agent_platform": "linux",
                        "status": "online" if state == "running" else "offline",
                        "is_cloud": True,
                        "is_physical": False,
                        "cpu": 15.0,
                        "mem": 42.0,
                        "disk": 20.0,
                    })
                    if new_id not in fleet_history:
                        fleet_history[new_id] = collections.deque(maxlen=HISTORY_LEN)
    except Exception as exc:
        logger.debug("Live AWS sync note: %s", exc)


def background_loop() -> None:
    psutil.cpu_percent(interval=0.5)
    for _ in range(10):
        generate_fleet_snapshots()
        time.sleep(0.1)

    sync_live_aws_instances()
    iter_count = 0

    while True:
        try:
            generate_fleet_snapshots()
            iter_count += 1
            if iter_count % 15 == 0:
                sync_live_aws_instances()

            logger.info(
                "Streaming 8 Fleet Nodes -> L1 (Physical): %4.1f%% | AWS-01 (Live): %4.1f%% | AWS-02: %4.1f%% | AWS-GW: %4.1f%%",
                fleet_history["host-laptop-01"][-1]["cpu"],
                fleet_history["aws-worker-01"][-1]["cpu"],
                fleet_history["aws-worker-02"][-1]["cpu"],
                fleet_history["aws-gateway-01"][-1]["cpu"],
            )
        except Exception as e:
            logger.error("Simulator error: %s", e)
        time.sleep(2.0)


class MultiLaptopHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status_code: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, POST, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS, POST, PUT, DELETE")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:
        clean = self.path.split("?")[0]
        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len) if content_len > 0 else b"{}"
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        # Permission Gate: POST /incidents/{id}/approve
        if "/approve" in clean:
            parts = clean.strip("/").split("/")
            inc_id = parts[-2] if len(parts) >= 2 else parts[0]
            try:
                action_ids = body.get("action_ids")
                decided_by = body.get("decided_by", "Operator")
                comment = body.get("comment", "")
                dry_run = body.get("dry_run", True)

                updated = incident_store.approve_and_execute(
                    incident_id=inc_id,
                    action_ids=action_ids,
                    decided_by=decided_by,
                    comment=comment,
                    dry_run=dry_run,
                )
                active_anomalies.clear()
                generate_fleet_snapshots()
                self._send_json(updated, 200)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
                return

        # Permission Gate: POST /incidents/{id}/reject
        if "/reject" in clean:
            parts = clean.strip("/").split("/")
            inc_id = parts[-2] if len(parts) >= 2 else parts[0]
            try:
                decided_by = body.get("decided_by", "Operator")
                comment = body.get("comment", "")

                updated = incident_store.reject_action(
                    incident_id=inc_id,
                    decided_by=decided_by,
                    comment=comment,
                )
                self._send_json(updated, 200)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
                return

        # Rollback: POST /incidents/{id}/rollback
        if "/rollback" in clean:
            parts = clean.strip("/").split("/")
            inc_id = parts[-2] if len(parts) >= 2 else parts[0]
            try:
                decided_by = body.get("decided_by", "Operator")
                comment = body.get("comment", "")
                dry_run = body.get("dry_run", True)

                updated = incident_store.rollback_action(
                    incident_id=inc_id,
                    decided_by=decided_by,
                    comment=comment,
                    dry_run=dry_run,
                )
                self._send_json(updated, 200)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
                return

        # Anomaly Injection: POST /demo/inject or /api/v1/demo/inject
        if clean in ("/demo/inject", "/api/v1/demo/inject"):
            host_id = body.get("host_id", "aws-worker-01")
            attack_type = body.get("attack_type", "ddos").lower()

            host_label_map = {
                "aws-worker-01": "AdaptiveCloud-Worker-01 (i-017c3c1add524779c)",
                "aws-worker-02": "AdaptiveCloud-Worker-02 (i-0ab2c3d4e5f678901)",
                "aws-gateway-01": "AWS Cloud Ingress Gateway (i-09f1a238e5b4c10aa)",
                "aws-db-01": "AWS RDS Database Primary (i-0bb8214f9d0c24e12)",
                "host-laptop-01": f"Local Host ({HOSTNAME})",
                "host-laptop-02": "Lab Workstation A (Simulated)",
                "host-laptop-03": "Dev Workstation B (Simulated Linux)",
                "host-laptop-04": "Field Workstation C (Simulated)",
            }
            target_host = host_label_map.get(host_id, f"AWS Node ({host_id})")

            try:
                from scripts.aws_cloud_monitor import trigger_aws_incident
                inc = trigger_aws_incident(
                    attack_type=attack_type,
                    target_host=target_host,
                )
            except Exception as exc:
                inc = {"incident_id": f"inc-aws-manual-{int(time.time())}", "error": str(exc)}

            if attack_type == "ddos":
                active_anomalies[host_id] = {
                    "cpu": 93.8,
                    "mem": 78.4,
                    "conn_count": 520,
                    "type": "ddos",
                    "processes": [
                        {"name": "syn_flood_ingress", "pid": 9811, "cpu_percent": 84.5},
                        {"name": "iptables_drop", "pid": 9812, "cpu_percent": 7.4},
                    ],
                }
            elif attack_type == "cryptomining":
                active_anomalies[host_id] = {
                    "cpu": 98.6,
                    "mem": 86.2,
                    "conn_count": 45,
                    "type": "cryptomining",
                    "processes": [
                        {"name": "xmrig_miner", "pid": 9941, "cpu_percent": 89.4},
                        {"name": "stratum_daemon", "pid": 9942, "cpu_percent": 8.1},
                    ],
                }
            elif attack_type == "brute_force":
                active_anomalies[host_id] = {
                    "cpu": 52.0,
                    "mem": 58.0,
                    "conn_count": 185,
                    "type": "brute_force",
                    "processes": [
                        {"name": "sshd_auth_fail", "pid": 9710, "cpu_percent": 34.0},
                        {"name": "hydra_spray", "pid": 9711, "cpu_percent": 12.0},
                    ],
                }
            else:
                active_anomalies[host_id] = {
                    "cpu": 85.0,
                    "mem": 88.0,
                    "conn_count": 95,
                    "type": attack_type,
                    "processes": [
                        {"name": "sql_inject_probe", "pid": 9601, "cpu_percent": 74.0},
                    ],
                }

            # Force immediate telemetry snapshot refresh across fleet
            generate_fleet_snapshots()

            self._send_json({
                "success": True,
                "incident": inc,
                "active_anomaly": active_anomalies[host_id],
            }, 200)
            return

        # Anomaly Resolver: POST /demo/resolve or /api/v1/demo/resolve
        if clean in ("/demo/resolve", "/api/v1/demo/resolve"):
            host_id = body.get("host_id", "aws-worker-01")
            active_anomalies.pop(host_id, None)
            generate_fleet_snapshots()
            self._send_json({"success": True, "status": "normal"}, 200)
            return

        # Autonomous Instant Self-Healing: POST /demo/heal or /api/v1/demo/heal or /heal
        if clean in ("/demo/heal", "/api/v1/demo/heal", "/heal", "/api/v1/heal") or clean.endswith("/auto_heal"):
            inc_id = body.get("incident_id")
            host_id = body.get("host_id", "aws-worker-01")
            active_anomalies.clear()
            healed = incident_store.auto_heal(inc_id)
            generate_fleet_snapshots()
            self._send_json({
                "success": True,
                "status": "healed",
                "incident": healed,
                "message": "Autonomous self-healing completed. Threat neutralized without operator delay.",
            }, 200)
            return

        self._send_json({"error": "Endpoint not found"}, 404)

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        clean = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        # GET /incidents or /api/v1/incidents
        if clean in ("/incidents", "/api/v1/incidents"):
            incident_store.check_expirations(timeout_seconds=3600)
            family = query_params.get("family", [None])[0]
            status_param = query_params.get("status", [None])[0]
            source = query_params.get("source", [None])[0]
            host_id_param = query_params.get("host_id", [None])[0]
            limit_param = int(query_params.get("limit", ["100"])[0])

            items = incident_store.list_incidents(
                family=family,
                status=status_param,
                source=source,
                host_id=host_id_param,
                limit=limit_param,
            )
            self._send_json(items)
            return

        # GET /incidents/{id}
        if clean.startswith("/incidents/") or clean.startswith("/api/v1/incidents/"):
            parts = clean.strip("/").split("/")
            inc_id = parts[-1]
            inc = incident_store.get_incident(inc_id)
            if inc:
                self._send_json(inc)
            else:
                self._send_json({"error": f"Incident {inc_id} not found"}, 404)
            return

        if clean in ("/", "/info", "/status"):
            info = {
                "status": "online",
                "hostname": HOSTNAME,
                "ip_address": LOCAL_IP,
                "os_version": OS_DETAILS,
                "is_physical": True,
                "active_laptops": 4,
            }
            self._send_json(info)
            return

        if clean in ("/hosts", "/api/v1/hosts"):
            # Pull live readings from fleet history
            with fleet_lock:
                l1 = fleet_history["host-laptop-01"][-1] if fleet_history["host-laptop-01"] else {}
                l2 = fleet_history["host-laptop-02"][-1] if fleet_history["host-laptop-02"] else {}
                l3 = fleet_history["host-laptop-03"][-1] if fleet_history["host-laptop-03"] else {}
                l4 = fleet_history["host-laptop-04"][-1] if fleet_history["host-laptop-04"] else {}
                aws1 = fleet_history["aws-worker-01"][-1] if fleet_history["aws-worker-01"] else {}

            hosts_list = [
                {
                    "id": "host-laptop-01",
                    "hostname": HOSTNAME,
                    "display_label": f"Local Host ({HOSTNAME})",
                    "os_version": OS_DETAILS,
                    "agent_platform": "windows",
                    "ip_address": LOCAL_IP,
                    "status": "online",
                    "is_physical": True,
                    "is_cloud": False,
                    "cpu": round(l1.get("cpu", 25), 1),
                    "mem": round(l1.get("mem", 52), 1),
                    "disk": round(l1.get("disk", 45), 1),
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "aws-worker-01",
                    "hostname": "AdaptiveCloud-Worker-01",
                    "display_label": "AWS EC2 Worker 01 (i-017c3c1add524779c)",
                    "os_version": "Amazon Linux 2023 (ap-south-1b · Mumbai)",
                    "agent_platform": "linux",
                    "ip_address": "3.108.250.115",
                    "status": "online",
                    "is_physical": False,
                    "is_cloud": True,
                    "cpu": round(aws1.get("cpu", 18.2), 1),
                    "mem": round(aws1.get("mem", 44.5), 1),
                    "disk": round(aws1.get("disk", 22.8), 1),
                    "instance_id": "i-017c3c1add524779c",
                    "region": "ap-south-1b (Mumbai)",
                    "type": "t2.micro (Free Tier)",
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "aws-worker-02",
                    "hostname": "AdaptiveCloud-Worker-02",
                    "display_label": "AWS EC2 Worker 02 (ap-south-1a)",
                    "os_version": "Amazon Linux 2023 (ap-south-1a · Mumbai)",
                    "agent_platform": "linux",
                    "ip_address": "13.233.142.76",
                    "status": "online",
                    "is_physical": False,
                    "is_cloud": True,
                    "cpu": round(14.0 + 2.0 * ((time.time() / 7) % 2 - 1), 1),
                    "mem": 38.2,
                    "disk": 19.5,
                    "instance_id": "i-0ab2c3d4e5f678901",
                    "region": "ap-south-1a (Mumbai)",
                    "type": "t2.micro (Free Tier)",
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "host-laptop-02",
                    "hostname": "LAB-WORKSTATION-A",
                    "display_label": "Lab Workstation A (Simulated)",
                    "os_version": "Windows 11 Enterprise",
                    "agent_platform": "windows",
                    "ip_address": "192.168.1.102",
                    "status": "online",
                    "is_physical": True,
                    "is_cloud": False,
                    "cpu": round(l2.get("cpu", 64), 1),
                    "mem": round(l2.get("mem", 72), 1),
                    "disk": 68,
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "host-laptop-03",
                    "hostname": "DEV-WORKSTATION-B",
                    "display_label": "Dev Workstation B (Simulated Linux)",
                    "os_version": "Ubuntu 24.04 LTS",
                    "agent_platform": "linux",
                    "ip_address": "192.168.1.103",
                    "status": "online",
                    "is_physical": True,
                    "is_cloud": False,
                    "cpu": round(l3.get("cpu", 94), 1),
                    "mem": round(l3.get("mem", 86), 1),
                    "disk": 82,
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "id": "host-laptop-04",
                    "hostname": "FIELD-WORKSTATION-C",
                    "display_label": "Field Workstation C (Simulated)",
                    "os_version": "Windows 10 Pro",
                    "agent_platform": "windows",
                    "ip_address": "192.168.1.104",
                    "status": "online",
                    "is_physical": True,
                    "is_cloud": False,
                    "cpu": round(l4.get("cpu", 42), 1),
                    "mem": round(l4.get("mem", 68), 1),
                    "disk": 55,
                    "is_active": True,
                    "last_seen": datetime.now(timezone.utc).isoformat(),
                },
            ]
            # Dynamically append all AWS workers registered in registered_aws_workers
            existing_ids = {h["id"] for h in hosts_list}
            for aw in registered_aws_workers:
                if aw["id"] not in existing_ids:
                    with fleet_lock:
                        last_snap = fleet_history[aw["id"]][-1] if (aw["id"] in fleet_history and fleet_history[aw["id"]]) else {}
                    aw_entry = {
                        **aw,
                        "cpu": round(last_snap.get("cpu", aw.get("cpu", 15.0)), 1),
                        "mem": round(last_snap.get("mem", aw.get("mem", 40.0)), 1),
                        "disk": round(last_snap.get("disk", aw.get("disk", 20.0)), 1),
                        "last_seen": datetime.now(timezone.utc).isoformat(),
                    }
                    hosts_list.append(aw_entry)

            self._send_json(hosts_list)
            return

        if clean in ("/peers", "/peer-laptops"):
            peers = {
                "host-laptop-02": {
                    "hostname": "LAB-WORKSTATION-A",
                    "display_label": "Lab Workstation A (Physical)",
                    "ip_address": "192.168.1.102",
                    "os_version": "Windows 11 Enterprise",
                    "cpu": 64,
                    "mem": 72,
                },
                "host-laptop-03": {
                    "hostname": "DEV-WORKSTATION-B",
                    "display_label": "Dev Workstation B (Physical Linux)",
                    "ip_address": "192.168.1.103",
                    "os_version": "Ubuntu 24.04 LTS",
                    "cpu": 94,
                    "mem": 86,
                },
                "host-laptop-04": {
                    "hostname": "FIELD-WORKSTATION-C",
                    "display_label": "Field Workstation C (Physical)",
                    "ip_address": "192.168.1.104",
                    "os_version": "Windows 10 Pro",
                    "cpu": 42,
                    "mem": 68,
                },
            }
            self._send_json(peers)
            return

        for card_id in list(fleet_history.keys()):
            if (
                clean == f"/hosts/{card_id}/metrics"
                or clean == f"/api/v1/hosts/{card_id}/metrics"
                or clean.endswith(f"/hosts/{card_id}/metrics")
                or clean == f"/{card_id}/telemetry"
                or clean == f"/api/v1/{card_id}/telemetry"
                or (card_id == "host-laptop-01" and clean in ("/telemetry", "/api/v1/telemetry"))
            ):
                with fleet_lock:
                    pts = list(fleet_history[card_id])
                payload = {
                    "host_id": card_id,
                    "status": "online",
                    "points": pts,
                    "latest": pts[-1] if pts else {},
                }
                self._send_json(payload)
                return

        self._send_json({"error": "Not found"}, 404)

    def log_message(self, format: str, *args: Any) -> None:
        pass


def seed_initial_incidents() -> None:
    """Pre-seed representative incidents covering all sources, families, and approval statuses."""
    existing = incident_store.list_incidents(limit=5)
    if len(existing) >= 3:
        return

    logger.info("Initializing baseline incidents in SQLite store...")
    samples = [
        {
            "incident_id": "inc-live-001",
            "source": "live",
            "host_id": "PHYSICAL-LAPTOP-01 (Host Laptop - Windows 11)",
            "tier1_family": "brute_force",
            "tier1_confidence": 0.968,
            "tier2_technique": "T1110.004 (Credential Stuffing)",
            "tier2_confidence": 0.942,
            "status": "awaiting_approval",
            "features": {"cpu": 24.5, "ram": 52.0, "failed_logins": 42, "inbound_traffic": 140.0, "active_connections": 54, "src_ip": "198.51.100.45"},
            "approval": {"decided_by": None, "decision": None, "decided_at": None, "comment": None},
            "execution_log": [],
            "outcome_summary": "High-confidence credential attack detected. Awaiting operator authorization before firewall block.",
        },
        {
            "incident_id": "inc-sim-002",
            "source": "simulated",
            "host_id": "GCP-VM-EU-02 (Google Cloud VPC Gateway)",
            "tier1_family": "ddos",
            "tier1_confidence": 0.985,
            "tier2_technique": "T1498.001 (Direct Network Flood)",
            "tier2_confidence": 0.970,
            "status": "verified",
            "features": {"cpu": 82.4, "ram": 64.0, "failed_logins": 0, "inbound_traffic": 94000.0, "active_connections": 380, "src_ip": "198.51.100.88"},
            "approval": {"decided_by": "SecOps Lead", "decision": "approved", "decided_at": "2026-11-15T02:00:00Z", "comment": "Approved Cloud Armor edge rate-limit."},
            "execution_log": [
                {
                    "action_id": "ACT_GCP_ARMOR_RATE_LIMIT",
                    "command": "gcloud compute security-policies rules create 1000 --security-policy=cloud-armor-adaptive-waf --src-ip-ranges=198.51.100.0/24 --action=rate-based-ban",
                    "dry_run": True,
                    "status": "simulated",
                    "result": "Rate-limit policy deployed across Google edge POPs in 380ms.",
                    "duration_ms": 380.0,
                    "executed_at": "2026-11-15T02:00:01Z",
                }
            ],
            "verification_result": {
                "verified": True,
                "probe": "GCP Cloud Monitoring Edge Packet Probe",
                "metrics_before": {"inbound_traffic_pps": 94000},
                "metrics_after": {"inbound_traffic_pps": 110},
                "message": "Traffic rate normalized to 110 pkts/s (99.8% reduction).",
            },
            "outcome_summary": "Approved by SecOps Lead. Cloud Armor edge rate-limit verified active.",
        },
        {
            "incident_id": "inc-sim-003",
            "source": "simulated",
            "host_id": "PHYSICAL-LAPTOP-03 (Dev Workstation B - Ubuntu)",
            "tier1_family": "cryptomining",
            "tier1_confidence": 0.975,
            "tier2_technique": "T1496 (Resource Hijacking)",
            "tier2_confidence": 0.960,
            "status": "awaiting_approval",
            "features": {"cpu": 94.2, "ram": 86.0, "failed_logins": 0, "inbound_traffic": 180.0, "active_connections": 45, "pid": 4912, "process_name": "xmrig"},
            "approval": {"decided_by": None, "decision": None, "decided_at": None, "comment": None},
            "execution_log": [],
            "outcome_summary": "Rogue mining daemon identified consuming 94% CPU. Awaiting permission to terminate PID 4912.",
        },
        {
            "incident_id": "inc-live-004",
            "source": "live",
            "host_id": "PHYSICAL-LAPTOP-04 (Field Workstation C)",
            "tier1_family": "privilege_escalation",
            "tier1_confidence": 0.964,
            "tier2_technique": "T1003.001 (LSASS Memory Dump)",
            "tier2_confidence": 0.935,
            "status": "rejected",
            "features": {"cpu": 48.0, "ram": 62.0, "failed_logins": 2, "inbound_traffic": 110.0, "active_connections": 22},
            "approval": {"decided_by": "Compliance Officer", "decision": "rejected", "decided_at": "2026-11-15T01:45:00Z", "comment": "Authorized internal red team penetration test. No action permitted."},
            "execution_log": [],
            "outcome_summary": "Operator rejected countermeasure. Host remains uninhibited for audit.",
        },
        {
            "incident_id": "inc-sim-005",
            "source": "simulated",
            "host_id": "PHYSICAL-LAPTOP-02 (Lab Workstation A)",
            "tier1_family": "port_scan",
            "tier1_confidence": 0.924,
            "tier2_technique": "T1046 (Network Service Scanning)",
            "tier2_confidence": 0.910,
            "status": "expired",
            "features": {"cpu": 22.0, "ram": 48.0, "failed_logins": 0, "inbound_traffic": 340.0, "active_connections": 185},
            "approval": {"decided_by": "System Watchdog", "decision": "expired", "decided_at": "2026-11-15T01:30:00Z", "comment": "Approval window elapsed without human authorization."},
            "execution_log": [],
            "outcome_summary": "Permission gate timed out (300s). No defensive action taken.",
        },
    ]

    for s in samples:
        rca = rca_engine.analyze(
            features=s["features"],
            tier1_family=s["tier1_family"],
            tier1_confidence=s["tier1_confidence"],
            tier2_technique=s["tier2_technique"],
            tier2_confidence=s["tier2_confidence"],
            host_id=s["host_id"],
        )
        s["rca"] = rca
        s["recommended_actions"] = rca["recommended_actions"]
        incident_store.save_incident(s)


def main() -> None:
    banner = f"""
======================================================================
      ADAPTIVECLOUD MULTI-LAPTOP FLEET SIMULATOR v2.5.0
======================================================================
  [+] Host Laptop (You) : {HOSTNAME} ({LOCAL_IP})
  [+] Simulated Fleet   : 4 Physical Laptops Streaming Simultaneously!
  [+] Hub API Port      : http://localhost:{PORT}
  [+] Status            : ALL 4 CARDS ON YOUR SCREEN ARE NOW LIVE!
======================================================================
"""
    print(banner)

    seed_initial_incidents()

    collector_thread = threading.Thread(target=background_loop, daemon=True)
    collector_thread.start()

    server = HTTPServer((HOST, PORT), MultiLaptopHandler)
    logger.info("Serving all 4 laptops on port %d...", PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSimulator stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
