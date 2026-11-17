"""
scripts/inject_live_anomaly.py
Live Interactive Anomaly Injector for AdaptiveCloud Security & AWS Cloud Node.
Directly injects a realistic cyber anomaly into the live telemetry stream:
- Injects anomaly on AWS EC2 Worker 01 (i-017c3c1add524779c)
- Spikes real-time telemetry (CPU, RAM, Inbound Traffic, Sockets)
- Generates a verified incident in SQLite (data/incidents.db)
- Triggers immediate real-time update on http://localhost:5173/

Usage:
    python scripts/inject_live_anomaly.py --type ddos
    python scripts/inject_live_anomaly.py --type cryptomining
    python scripts/inject_live_anomaly.py --type brute_force
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

API_URL = "http://localhost:8001/api/v1/demo/inject"


def inject_anomaly(attack_type: str = "ddos", host_id: str = "aws-worker-01") -> None:
    print("\n" + "=" * 65)
    print("   ADAPTIVECLOUD - LIVE AWS CLOUD ANOMALY INJECTION HARNESS   ")
    print("=" * 65)
    print(f"[*] Target Cloud Node: {host_id} (AdaptiveCloud-Worker-01 - AWS Mumbai)")
    print(f"[*] Anomaly Family   : {attack_type.upper()}")
    print(f"[*] Timestamp        : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    payload = json.dumps({
        "host_id": host_id,
        "attack_type": attack_type,
    }).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            inc = res_data.get("incident", {})
            anom = res_data.get("active_anomaly", {})

            print("[✓] SUCCESS: Anomaly Injected & Registered in Live Telemetry Stream!")
            print(f"    - Incident ID : {inc.get('incident_id')}")
            print(f"    - Threat Family: {inc.get('tier1_family')}")
            print(f"    - MITRE Technique: {inc.get('tier2_technique')}")
            print(f"    - Confidence   : {inc.get('tier1_confidence', 0.95) * 100:.1f}%")
            print(f"    - Telemetry Spike: CPU={anom.get('cpu')}% | RAM={anom.get('mem')}% | Conns={anom.get('conn_count')}")
            print("-" * 65)
            print(">>> LIVE DASHBOARD ACTIONS:")
            print("1. Open http://localhost:5173/ -> Observe AWS EC2 Worker turn RED (High Load)!")
            print("2. Open http://localhost:5173/rca -> Inspect Root Cause Analysis & Evidence Multipliers.")
            print("3. Open http://localhost:5173/healing -> Click [Approve] to execute self-healing playbook!")
            print("   (Approving will automatically mitigate the attack and return CPU to normal baseline)")
            print("=" * 65 + "\n")

    except urllib.error.URLError as e:
        print(f"[!] Error: Could not connect to Telemetry Hub at {API_URL}. Is it running? ({e})")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inject live anomaly into AWS Cloud node.")
    parser.add_argument(
        "--type",
        choices=["ddos", "cryptomining", "brute_force", "web_attack"],
        default="ddos",
        help="Type of cyber anomaly to trigger (default: ddos)",
    )
    parser.add_argument(
        "--host",
        default="aws-worker-01",
        help="Target host ID (default: aws-worker-01)",
    )
    args = parser.parse_args()
    inject_anomaly(attack_type=args.type, host_id=args.host)
