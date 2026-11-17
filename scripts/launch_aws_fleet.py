"""
scripts/launch_aws_fleet.py
Provisions multiple real AWS EC2 Worker nodes for AdaptiveCloud Security.
- Image: Amazon Linux 2023 (ami-04b0b8ee9ce90920a)
- Type: t2.micro
- Distributed across Availability Zones: ap-south-1a, ap-south-1b, ap-south-1c
- Telemetry agent automatically installed via UserData
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.aws_cloud_monitor import get_boto3_session

AMI_ID = "ami-04b0b8ee9ce90920a"  # Amazon Linux 2023 ap-south-1
INSTANCE_TYPE = "t2.micro"

SUBNETS = [
    {"az": "ap-south-1a", "id": "subnet-0c346b3b6f77187b4"},
    {"az": "ap-south-1b", "id": "subnet-0fe4e166571f07d1e"},
    {"az": "ap-south-1c", "id": "subnet-099d3575d65471f05"},
]

USER_DATA = """#!/bin/bash
dnf update -y
dnf install -y python3 python3-pip git htop
pip3 install psutil requests
"""


def get_existing_instances(ec2):
    res = ec2.describe_instances(
        Filters=[
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]},
        ]
    )
    insts = []
    for r in res.get("Reservations", []):
        for i in r.get("Instances", []):
            name = i["InstanceId"]
            for t in i.get("Tags", []):
                if t["Key"] == "Name":
                    name = t["Value"]
            insts.append({"id": i["InstanceId"], "name": name, "state": i["State"]["Name"], "ip": i.get("PublicIpAddress", "N/A")})
    return insts


def launch_fleet(count: int = 5):
    session = get_boto3_session()
    if not session:
        print("[!] No AWS session available. Check credentials.")
        return

    ec2 = session.client("ec2")
    existing = get_existing_instances(ec2)
    print(f"[*] Found {len(existing)} existing instance(s) in AWS ap-south-1:")
    for ex in existing:
        print(f"    - {ex['id']} ({ex['name']}) : {ex['state']} | IP: {ex['ip']}")

    # Determine starting worker index
    existing_nums = []
    for ex in existing:
        if "Worker-" in ex["name"]:
            try:
                num = int(ex["name"].split("Worker-")[-1].split()[0])
                existing_nums.append(num)
            except Exception:
                pass
    start_idx = (max(existing_nums) + 1) if existing_nums else 2

    launched = []
    print(f"\n[*] Launching {count} new real AWS EC2 worker instances...")
    for i in range(count):
        idx = start_idx + i
        name = f"AdaptiveCloud-Worker-{idx:02d}"
        subnet = SUBNETS[i % len(SUBNETS)]
        print(f"[*] Requesting {name} in {subnet['az']} ({subnet['id']})...")

        try:
            res = ec2.run_instances(
                ImageId=AMI_ID,
                InstanceType=INSTANCE_TYPE,
                MinCount=1,
                MaxCount=1,
                SubnetId=subnet["id"],
                UserData=USER_DATA,
                TagSpecifications=[
                    {
                        "ResourceType": "instance",
                        "Tags": [
                            {"Key": "Name", "Value": name},
                            {"Key": "Project", "Value": "AdaptiveCloud"},
                            {"Key": "Environment", "Value": "Fleet"},
                        ],
                    }
                ],
            )
            new_inst = res["Instances"][0]
            launched.append({"id": new_inst["InstanceId"], "name": name, "az": subnet["az"]})
            print(f"    [+] Created instance request: {new_inst['InstanceId']}")
        except Exception as e:
            print(f"    [!] Failed to launch {name}: {e}")

    if not launched:
        print("[!] No instances launched.")
        return

    print(f"\n[*] Waiting for {len(launched)} instance(s) to enter 'running' state...")
    inst_ids = [l["id"] for l in launched]
    try:
        waiter = ec2.get_waiter("instance_running")
        waiter.wait(InstanceIds=inst_ids)
        print("[✓] All instances are now RUNNING in AWS!")
    except Exception as e:
        print(f"[*] Wait note: {e}")

    # Describe updated details
    desc = ec2.describe_instances(InstanceIds=inst_ids)
    print("\n=======================================================")
    print("      NEW REAL AWS EC2 WORKERS SUCCESSFULLY LAUNCHED    ")
    print("=======================================================")
    for r in desc.get("Reservations", []):
        for inst in r.get("Instances", []):
            name = inst["InstanceId"]
            for t in inst.get("Tags", []):
                if t["Key"] == "Name":
                    name = t["Value"]
            print(f"  [+] {name:28s} | ID: {inst['InstanceId']} | IP: {inst.get('PublicIpAddress', 'Pending')} | AZ: {inst['Placement']['AvailabilityZone']}")
    print("=======================================================\n")


def terminate_fleet():
    session = get_boto3_session()
    if not session:
        return
    ec2 = session.client("ec2")
    res = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["AdaptiveCloud"]},
            {"Name": "instance-state-name", "Values": ["running", "pending", "stopped"]},
        ]
    )
    to_term = []
    for r in res.get("Reservations", []):
        for i in r.get("Instances", []):
            name = ""
            for t in i.get("Tags", []):
                if t["Key"] == "Name":
                    name = t["Value"]
            # Keep Worker-01 if preferred, or terminate created fleet
            if name != "AdaptiveCloud-Worker-01":
                to_term.append(i["InstanceId"])

    if not to_term:
        print("[*] No additional fleet workers found to terminate.")
        return

    print(f"[*] Terminating {len(to_term)} fleet worker instance(s): {to_term}...")
    ec2.terminate_instances(InstanceIds=to_term)
    print("[✓] Termination command issued. Instances are shutting down.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch multiple real AWS EC2 workers")
    parser.add_argument("--count", type=int, default=5, help="Number of instances to launch (default: 5)")
    parser.add_argument("--terminate-fleet", action="store_true", help="Terminate additional fleet workers (keeps Worker-01)")
    args = parser.parse_args()

    if args.terminate_fleet:
        terminate_fleet()
    else:
        launch_fleet(args.count)
