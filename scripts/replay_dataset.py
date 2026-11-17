"""
scripts/replay_dataset.py
Replay and Historical Attack Ingestion Engine for AdaptiveCloud.
Processes the dataset / taxonomy (ml/data/cloud_attacks_238.csv) through Tier 1 and Tier 2 classifiers.
Creates permanent, immutable Incident Records with:
- source = 'dataset_replay'
- status = 'recorded' (Zero autonomous execution)
- Full RCA and scoped healing recommendations
- Aggregation / de-duplication of repeated attacks
- Export to JSON / CSV and terminal summary report.

Usage:
    python scripts/replay_dataset.py --limit 50 --sample-per-family 5 --seed 42
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.incident_store import incident_store
from core.rca_engine import rca_engine
from core.tier_classifiers import tier_classifiers

TAXONOMY_PATH = _REPO_ROOT / "ml" / "data" / "cloud_attacks_238.csv"
OUTPUT_DIR = _REPO_ROOT / "data" / "reports"


def simulate_features_for_attack(row: dict[str, Any], seed: int = 42) -> dict[str, Any]:
    """
    Generates realistic 5-feature behavioral telemetry derived from the attack's taxonomy row.
    """
    category = (row.get("category") or "").lower()
    fam = (row.get("canonical_family") or "").lower()
    tactic = (row.get("mitre_tactic") or "").lower()

    # Default baseline
    feats = {
        "cpu": round(random.uniform(10.0, 22.0), 1),
        "ram": round(random.uniform(35.0, 50.0), 1),
        "failed_logins": 0,
        "inbound_traffic": round(random.uniform(80.0, 150.0), 1),
        "active_connections": random.randint(15, 30),
    }

    if "brute" in category or fam == "brute_force" or "credential" in tactic:
        feats["failed_logins"] = random.randint(25, 120)
        feats["active_connections"] = random.randint(35, 75)
    elif "dos" in category or "ddos" in fam or "flood" in row.get("attack_name", "").lower():
        feats["inbound_traffic"] = round(random.uniform(8500.0, 95000.0), 1)
        feats["active_connections"] = random.randint(120, 450)
        feats["cpu"] = round(random.uniform(65.0, 92.0), 1)
    elif "scan" in category or fam == "port_scan" or "discovery" in tactic:
        feats["active_connections"] = random.randint(75, 200)
        feats["inbound_traffic"] = round(random.uniform(200.0, 400.0), 1)
    elif "crypto" in category or fam == "cryptomining":
        feats["cpu"] = round(random.uniform(88.0, 99.0), 1)
        feats["ram"] = round(random.uniform(70.0, 88.0), 1)
        feats["active_connections"] = random.randint(20, 50)
    elif "privilege" in tactic or fam == "privilege_escalation":
        feats["cpu"] = round(random.uniform(45.0, 75.0), 1)
        feats["lsass_probe"] = True
    elif "web" in category or fam == "web_attack":
        feats["inbound_traffic"] = round(random.uniform(450.0, 1200.0), 1)
        feats["active_connections"] = random.randint(45, 90)
        feats["sqli_signature"] = True
    elif "iam" in category or fam == "cloud_iam":
        feats["active_connections"] = random.randint(30, 60)
        feats["iam_privilege_abuse"] = True
    elif "storage" in category or fam == "cloud_storage" or "exfiltration" in tactic:
        feats["inbound_traffic"] = round(random.uniform(1500.0, 4500.0), 1)
        feats["bucket_egress_burst"] = True

    return feats


def run_dataset_replay(
    limit: int | None = None,
    sample_per_family: int | None = None,
    seed: int = 42,
    export_json: bool = True,
    export_csv: bool = True,
) -> dict[str, Any]:
    """Replays taxonomy/dataset through Tier 1 & Tier 2 classifiers."""
    random.seed(seed)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not TAXONOMY_PATH.exists():
        print(f"[!] Error: Taxonomy CSV not found at {TAXONOMY_PATH}")
        sys.exit(1)

    with open(TAXONOMY_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"[*] Loaded {len(rows)} entries from {TAXONOMY_PATH.name}")

    # Group by canonical family if sample_per_family requested
    if sample_per_family:
        family_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in rows:
            fam = r.get("canonical_family", "other").lower()
            family_buckets[fam].append(r)

        selected_rows: list[dict[str, Any]] = []
        for fam, items in family_buckets.items():
            selected_rows.extend(items[:sample_per_family])
        rows = selected_rows

    if limit and limit < len(rows):
        rows = rows[:limit]

    print(f"[*] Processing {len(rows)} attack candidates through Tier 1 & 2 classifiers...")

    # Aggregator for de-duplication of similar attacks
    aggregated_attacks: dict[str, dict[str, Any]] = {}
    family_counts: Counter[str] = Counter()
    root_cause_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    confidences: list[float] = []

    for idx, row in enumerate(rows, 1):
        attack_name = row.get("attack_name", f"Attack-{idx}")
        raw_tech = row.get("mitre_technique", "T1000")

        # Simulate 5-feature vector
        features = simulate_features_for_attack(row, seed=seed + idx)

        # Classify through Tier 1 & Tier 2
        clf_result = tier_classifiers.classify(features)
        t1_family = clf_result["tier1_family"]
        t1_conf = clf_result["tier1_confidence"]
        t2_tech = clf_result["tier2_technique"] or raw_tech
        t2_conf = clf_result["tier2_confidence"] or 0.85

        if t1_family == "benign":
            continue # Only record attacks

        # Generate RCA
        rca_result = rca_engine.analyze(
            features=features,
            tier1_family=t1_family,
            tier1_confidence=t1_conf,
            tier2_technique=t2_tech,
            tier2_confidence=t2_conf,
            host_id=f"DATASET-REPLAY-{row.get('id', idx)}",
            src_ip="198.51.100." + str(random.randint(10, 240)),
        )

        # Inject enriched row values if present
        ds_root_cause = row.get("root_cause_summary")
        ds_signal = row.get("primary_telemetry_signal")
        ds_playbook = row.get("self_healing_playbook_id")
        ds_action_name = row.get("remediation_action_name")
        ds_risk = row.get("risk_level", "low")
        ds_rev = row.get("reversible", "true").lower() == "true"

        probable_cause = f"Hypothesized Root Cause: {ds_root_cause}." if ds_root_cause else rca_result["probable_root_cause"]

        dedup_key = f"{t1_family}::{raw_tech}"

        if dedup_key in aggregated_attacks:
            aggregated_attacks[dedup_key]["repeat_count"] += 1
            aggregated_attacks[dedup_key]["sample_attack_names"].append(attack_name)
        else:
            inc_id = f"inc-ds-{int(row.get('id', idx)):03d}"
            record = {
                "incident_id": inc_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "dataset_replay",
                "host_id": f"DATASET-WORKSTATION-{row.get('id', idx)}",
                "attack_name": attack_name,
                "category": row.get("category", "General"),
                "mitre_technique": raw_tech,
                "features": features,
                "tier1_family": t1_family,
                "tier1_confidence": t1_conf,
                "tier2_technique": t2_tech,
                "tier2_confidence": t2_conf,
                "rca": {
                    "summary": f"Observed telemetry ({ds_signal or 'feature deviation'}) confirms {attack_name}. {probable_cause}",
                    "probable_root_cause": probable_cause,
                    "primary_telemetry_signal": ds_signal or "deviations",
                    "evidence": rca_result["evidence"],
                    "confidence": rca_result["confidence"],
                    "alternative_hypotheses": rca_result["alternative_hypotheses"],
                    "uncertainty_note": rca_result["uncertainty_note"],
                },
                "self_healing": {
                    "playbook_id": ds_playbook or "ACT_BLOCK_SOURCE_IP",
                    "playbook_name": ds_action_name or "Host Firewall Block",
                    "risk_level": ds_risk,
                    "reversible": ds_rev,
                    "target_layer": row.get("canonical_family", "host_os"),
                    "status": "ready_for_review",
                },
                "recommended_actions": rca_result["recommended_actions"],
                "status": "recorded", # NEVER executes autonomously
                "approval": {
                    "decided_by": "System (Historical Dataset)",
                    "decision": "archived",
                    "decided_at": datetime.now(timezone.utc).isoformat(),
                    "comment": f"Dataset replay record for {attack_name}. Stored permanently for training and offline compliance audit.",
                },
                "execution_log": [],
                "verification_result": None,
                "outcome_summary": f"Historical attack '{attack_name}' classified and permanently recorded in audit store.",
                "repeat_count": 1,
                "sample_attack_names": [attack_name],
            }
            aggregated_attacks[dedup_key] = record

            # Commit to SQLite persistent store
            incident_store.save_incident(record)

            # Statistics
            family_counts[t1_family] += 1
            root_cause_counts[rca_result["probable_root_cause"]] += 1
            for act in rca_result["recommended_actions"]:
                action_counts[act["name"]] += 1
            confidences.append(t1_conf)

    unique_records = list(aggregated_attacks.values())
    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0

    # Summary Report Object
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_records_processed": len(rows),
        "unique_incidents_recorded": len(unique_records),
        "average_confidence": round(avg_conf, 4),
        "attacks_per_family": dict(family_counts),
        "top_root_causes": dict(root_cause_counts.most_common(5)),
        "most_common_recommended_actions": dict(action_counts.most_common(5)),
    }

    # Export JSON
    if export_json:
        json_path = OUTPUT_DIR / "dataset_replay_records.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "summary": summary,
                "records": unique_records,
            }, f, indent=2)
        print(f"[+] Exported JSON records: {json_path}")

    # Export CSV
    if export_csv:
        csv_path = OUTPUT_DIR / "dataset_replay_summary.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Incident ID", "Family", "MITRE Technique", "Confidence", "Status", "Source", "Repeat Count", "Probable Root Cause"])
            for r in unique_records:
                writer.writerow([
                    r["incident_id"],
                    r["tier1_family"],
                    r["tier2_technique"],
                    r["tier1_confidence"],
                    r["status"],
                    r["source"],
                    r["repeat_count"],
                    r["rca"]["probable_root_cause"],
                ])
        print(f"[+] Exported CSV summary: {csv_path}")

    # Terminal Report Output
    print("\n" + "=" * 70)
    print("      ADAPTIVECLOUD DATASET REPLAY & HISTORICAL AUDIT REPORT")
    print("=" * 70)
    print(f"  [+] Total Candidates Replayed : {summary['total_records_processed']}")
    print(f"  [+] Unique Incidents Recorded : {summary['unique_incidents_recorded']}")
    print(f"  [+] Average Tier 1 Confidence : {summary['average_confidence'] * 100:.2f}%")
    print("----------------------------------------------------------------------")
    print("  ATTACKS PER CANONICAL FAMILY:")
    for fam, cnt in sorted(summary["attacks_per_family"].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {fam:<24} : {cnt} attacks")
    print("----------------------------------------------------------------------")
    print("  TOP IDENTIFIED ROOT CAUSES:")
    for cause, cnt in summary["top_root_causes"].items():
        print(f"    - [{cnt}x] {cause[:65]}...")
    print("----------------------------------------------------------------------")
    print("  TOP RECOMMENDED ACTIONS:")
    for act, cnt in summary["most_common_recommended_actions"].items():
        print(f"    - [{cnt}x] {act}")
    print("=" * 70 + "\n")

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="AdaptiveCloud Dataset Replay & Attack Ingestion")
    parser.add_argument("--limit", type=int, default=None, help="Max candidates to process")
    parser.add_argument("--sample-per-family", type=int, default=None, help="Max items per family")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    run_dataset_replay(
        limit=args.limit,
        sample_per_family=args.sample_per_family,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
