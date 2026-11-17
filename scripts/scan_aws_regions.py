import boto3
from pathlib import Path

env_lines = Path(".env").read_text(encoding="utf-8").splitlines()
creds = dict(line.split("=", 1) for line in env_lines if "=" in line and not line.startswith("#"))

session = boto3.Session(
    aws_access_key_id=creds["AWS_ACCESS_KEY_ID"],
    aws_secret_access_key=creds["AWS_SECRET_ACCESS_KEY"],
    region_name="ap-south-1",
)

regions = ["ap-south-1", "us-east-1", "us-east-2", "us-west-2", "eu-central-1"]
found_any = False

for r in regions:
    try:
        ec2 = session.client("ec2", region_name=r)
        res = ec2.describe_instances()
        instances = [inst for resv in res.get("Reservations", []) for inst in resv.get("Instances", [])]
        print(f"Region {r:12s}: {len(instances)} instance(s)")
        for inst in instances:
            found_any = True
            name = inst.get("InstanceId")
            for t in inst.get("Tags", []):
                if t.get("Key") == "Name":
                    name = t.get("Value")
            print(f"  [+] {name} ({inst.get('InstanceId')}) | State: {inst.get('State', {}).get('Name')} | IP: {inst.get('PublicIpAddress')}")
    except Exception as e:
        print(f"Region {r:12s}: {e}")

if not found_any:
    print("\n[!] No EC2 instances found across these regions.")

try:
    s3 = session.client("s3")
    buckets = s3.list_buckets().get("Buckets", [])
    print(f"\n[+] S3 Buckets ({len(buckets)}):")
    for b in buckets:
        print(f"    - {b['Name']}")
except Exception as e:
    print(f"\n[!] S3 check: {e}")
