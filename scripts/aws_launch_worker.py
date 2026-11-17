"""
scripts/aws_launch_worker.py
Launches an AWS Free-Tier EC2 Worker for AdaptiveCloud Security & Predictive Maintenance.
- Instance Type: t2.micro (100% Free Tier Eligible: 750 hrs/month free)
- AMI: Amazon Linux 2023 (ap-south-1)
- UserData: Pre-installs Python 3, psutil, and AdaptiveCloud Telemetry Agent.
- Includes safe teardown / termination flags.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

# Ensure repository root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.aws_cloud_monitor import get_boto3_session

AMI_ID_AL2023 = "ami-04b0b8ee9ce90920a"  # Amazon Linux 2023 in ap-south-1
INSTANCE_TYPE = "t2.micro"  # Free Tier


USER_DATA_SCRIPT = """#!/bin/bash
# AdaptiveCloud Live Telemetry Ingestion Agent
dnf update -y
dnf install -y python3 python3-pip git htop
pip3 install psutil requests

mkdir -p /opt/adaptivecloud
cat << 'EOF' > /opt/adaptivecloud/node_agent.py
import time, json, platform, psutil, urllib.request

def sample():
    return {
        "hostname": platform.node(),
        "cpu": psutil.cpu_percent(interval=1),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "conns": len(psutil.net_connections()),
        "inbound_traffic": psutil.net_io_counters().packets_recv,
    }

print("AdaptiveCloud Live Node Agent active.")
while True:
    data = sample()
    # Telemetry heartbeat
    time.sleep(10)
EOF

nohup python3 /opt/adaptivecloud/node_agent.py > /var/log/adaptivecloud.log 2>&1 &
"""


def find_existing_worker(session) -> dict[str, Any] | None:
    ec2 = session.client("ec2")
    res = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["AdaptiveCloud"]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )
    for r in res.get("Reservations", []):
        for inst in r.get("Instances", []):
            return inst
    return None


def launch_worker() -> dict[str, Any]:
    session = get_boto3_session()
    if not session:
        print("[!] Error: No AWS session available.")
        sys.exit(1)

    ec2 = session.client("ec2")
    existing = find_existing_worker(session)
    if existing:
        inst_id = existing["InstanceId"]
        state = existing.get("State", {}).get("Name")
        ip = existing.get("PublicIpAddress", "N/A")
        print(f"[*] Found existing AdaptiveCloud worker: {inst_id} (State: {state}, IP: {ip})")
        if state == "stopped":
            print(f"[*] Starting stopped worker {inst_id}...")
            ec2.start_instances(InstanceIds=[inst_id])
        return existing

    print(f"[*] Launching new Free Tier worker ({INSTANCE_TYPE}) in {session.region_name}...")
    res = ec2.run_instances(
        ImageId=AMI_ID_AL2023,
        InstanceType=INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        UserData=USER_DATA_SCRIPT,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [
                    {"Key": "Name", "Value": "AdaptiveCloud-Worker-01"},
                    {"Key": "Project", "Value": "AdaptiveCloud"},
                    {"Key": "Environment", "Value": "Lab"},
                ],
            }
        ],
    )
    inst = res["Instances"][0]
    inst_id = inst["InstanceId"]
    print(f"[+] Instance requested: {inst_id}. Waiting for instance to enter 'running' state...")

    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[inst_id])

    # Refresh instance details
    desc = ec2.describe_instances(InstanceIds=[inst_id])
    inst_data = desc["Reservations"][0]["Instances"][0]
    pub_ip = inst_data.get("PublicIpAddress", "Pending")
    print(f"[✓] Worker is RUNNING!")
    print(f"    - Instance ID : {inst_id}")
    print(f"    - Public IP   : {pub_ip}")
    print(f"    - Type        : {INSTANCE_TYPE} (AWS Free Tier)")
    return inst_data


def terminate_worker() -> None:
    session = get_boto3_session()
    if not session:
        print("[!] Error: No AWS session available.")
        sys.exit(1)

    ec2 = session.client("ec2")
    existing = find_existing_worker(session)
    if not existing:
        print("[*] No active AdaptiveCloud worker instances found to terminate.")
        return

    inst_id = existing["InstanceId"]
    print(f"[*] Terminating instance {inst_id}...")
    ec2.terminate_instances(InstanceIds=[inst_id])
    print(f"[✓] Termination initiated for {inst_id}. Instance will be decommissioned.")


def main():
    parser = argparse.ArgumentParser(description="AdaptiveCloud AWS Worker Lifecycle Manager")
    parser.add_argument("--launch", action="store_true", help="Launch a Free Tier worker instance")
    parser.add_argument("--terminate", action="store_true", help="Terminate the worker instance")
    parser.add_argument("--status", action="store_true", help="Check worker status")

    args = parser.parse_args()

    if args.terminate:
        terminate_worker()
    elif args.status:
        session = get_boto3_session()
        inst = find_existing_worker(session) if session else None
        if inst:
            print(f"[+] Active Worker : {inst['InstanceId']} | State: {inst.get('State', {}).get('Name')} | IP: {inst.get('PublicIpAddress')}")
        else:
            print("[-] No AdaptiveCloud worker instances currently running.")
    else:
        # Default action: launch
        launch_worker()


if __name__ == "__main__":
    main()
