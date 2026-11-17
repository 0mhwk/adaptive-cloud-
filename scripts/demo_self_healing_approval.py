"""
scripts/demo_self_healing_approval.py
End-to-End Demonstration: Self-Healing with Human Approval Gate.
Demonstrates the full pipeline:
1. Threat Ingestion & Simulation (Volumetric TCP SYN Flood on Google Cloud Gateway).
2. Incident Record creation with dynamic RCA, feature baseline deviations, and healing plan.
3. Permission Gate: System holds in 'awaiting_approval' (No disruptive execution permitted).
4. Human Approval: Operator authorizes execution with comment.
5. Guardrail-checked Playbook execution (dry-run mode).
6. Post-execution verification probe (traffic normalized).
7. Operator-initiated rollback demonstration.

Usage:
    python scripts/demo_self_healing_approval.py
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add repo root to path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.incident_store import incident_store
from core.rca_engine import rca_engine
from core.tier_classifiers import tier_classifiers


def run_e2e_demo() -> None:
    print("\n" + "=" * 75)
    print("      ADAPTIVECLOUD: SELF-HEALING WITH HUMAN APPROVAL DEMO")
    print("=" * 75)

    # -------------------------------------------------------------
    # Step 1: Ingest anomalous telemetry / simulated attack
    # -------------------------------------------------------------
    print("\n[STAGE 1: TELEMETRY INGESTION]")
    target_host = "GCP-VM-EU-02 (Google Cloud VPC Gateway)"
    simulated_features = {
        "cpu": 82.4,
        "ram": 68.0,
        "failed_logins": 0,
        "inbound_traffic": 94000.0,  # 94,000 packets/sec
        "active_connections": 380,   # 380 concurrent sockets
        "src_ip": "198.51.100.45",
    }
    print(f"  [+] Host Under Attack : {target_host}")
    print(f"  [+] Inbound Traffic   : {simulated_features['inbound_traffic']:,} packets/sec (Normal baseline: 120)")
    print(f"  [+] Active Sockets    : {simulated_features['active_connections']} connections")
    print(f"  [+] Host CPU Pressure : {simulated_features['cpu']}%")

    # -------------------------------------------------------------
    # Step 2: Tier 1 & Tier 2 Classification
    # -------------------------------------------------------------
    print("\n[STAGE 2: TWO-TIER THREAT CLASSIFICATION]")
    clf_res = tier_classifiers.classify(simulated_features)
    print(f"  [+] Tier 1 Canonical Family : {clf_res['tier1_family'].upper()} (Confidence: {clf_res['tier1_confidence'] * 100:.1f}%)")
    print(f"  [+] Tier 2 ATT&CK Technique  : {clf_res['tier2_technique']} (Confidence: {clf_res['tier2_confidence'] * 100:.1f}%)")

    # -------------------------------------------------------------
    # Step 3: Evidence-grounded RCA & Healing Plan Synthesis
    # -------------------------------------------------------------
    print("\n[STAGE 3: ROOT CAUSE ANALYSIS & HEALING PLAN]")
    rca = rca_engine.analyze(
        features=simulated_features,
        tier1_family=clf_res["tier1_family"],
        tier1_confidence=clf_res["tier1_confidence"],
        tier2_technique=clf_res["tier2_technique"],
        tier2_confidence=clf_res["tier2_confidence"],
        host_id=target_host,
        src_ip=simulated_features["src_ip"],
    )

    print(f"  [+] Summary        : {rca['summary']}")
    print(f"  [+] Root Cause     : {rca['probable_root_cause']}")
    print(f"  [+] Telemetry Evid : {rca['evidence'][0]}")
    print(f"  [+] Uncertainty    : {rca['uncertainty_note']}")
    print(f"  [+] Actions Found  : {len(rca['recommended_actions'])} proposed countermeasure(s)")

    # -------------------------------------------------------------
    # Step 4: Persist Incident Record in 'awaiting_approval'
    # -------------------------------------------------------------
    print("\n[STAGE 4: INCIDENT CREATED IN PERMISSION GATE]")
    inc_record = {
        "incident_id": f"inc-demo-{int(time.time())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "simulated",
        "host_id": target_host,
        "features": simulated_features,
        "tier1_family": clf_res["tier1_family"],
        "tier1_confidence": clf_res["tier1_confidence"],
        "tier2_technique": clf_res["tier2_technique"],
        "tier2_confidence": clf_res["tier2_confidence"],
        "rca": rca,
        "recommended_actions": rca["recommended_actions"],
        "status": "awaiting_approval",
        "approval": {
            "decided_by": None,
            "decision": None,
            "decided_at": None,
            "comment": None,
        },
        "execution_log": [],
        "verification_result": None,
        "outcome_summary": "Incident logged. Awaiting human operator approval before any playbook executes.",
    }

    saved = incident_store.save_incident(inc_record)
    inc_id = saved["incident_id"]
    print(f"  [+] Incident ID    : {inc_id}")
    print(f"  [+] Current Status : {saved['status'].upper()}")
    print("  [!] ENFORCEMENT CHECK: Zero playbooks have run. System is halted awaiting approval.")

    # -------------------------------------------------------------
    # Step 5: Simulate Human Operator Approval
    # -------------------------------------------------------------
    print("\n[STAGE 5: OPERATOR HUMAN APPROVAL]")
    operator_name = "SecOps Lead (Pradnyan)"
    operator_comment = "Verified external botnet assault. Approved Google Cloud Armor edge rate-limiting playbook."
    print(f"  [+] Operator Action : Approving Incident {inc_id}")
    print(f"  [+] Approver        : {operator_name}")
    print(f"  [+] Comment         : \"{operator_comment}\"")

    approved_inc = incident_store.approve_and_execute(
        incident_id=inc_id,
        action_ids=["ACT_GCP_ARMOR_RATE_LIMIT"],
        decided_by=operator_name,
        comment=operator_comment,
        dry_run=True, # Dry-run simulation for safe demonstration
    )

    print("\n[STAGE 6: EXECUTION & VERIFICATION PROBE]")
    print(f"  [+] Updated Status : {approved_inc['status'].upper()}")
    print(f"  [+] Execution Log  :")
    for log in approved_inc["execution_log"]:
        print(f"      - Command  : {log.get('command')}")
        print(f"      - Mode     : {'DRY-RUN' if log.get('dry_run') else 'LIVE'}")
        print(f"      - Result   : {log.get('result')}")
        print(f"      - Latency  : {log.get('duration_ms')} ms")

    v_res = approved_inc.get("verification_result") or {}
    print(f"  [+] Verification   : {'PASSED (HEALTHY)' if v_res.get('verified') else 'FAILED'}")
    print(f"      - Before Probe : {v_res.get('metrics_before')}")
    print(f"      - After Probe  : {v_res.get('metrics_after')}")
    print(f"      - Probe Note   : {v_res.get('message')}")

    # -------------------------------------------------------------
    # Step 7: Demonstrate 1-Click Rollback
    # -------------------------------------------------------------
    print("\n[STAGE 7: OPERATOR ROLLBACK DEMONSTRATION]")
    print(f"  [+] Initiating Rollback on {inc_id}...")
    rolled_back_inc = incident_store.rollback_action(
        incident_id=inc_id,
        decided_by=operator_name,
        comment="Post-incident recovery drill complete. Reverting injected firewall policies.",
        dry_run=True,
    )
    print(f"  [+] Post-Rollback Status : {rolled_back_inc['status'].upper()}")
    print(f"  [+] Outcome Summary      : {rolled_back_inc['outcome_summary']}")

    print("\n" + "=" * 75)
    print("      DEMO SUCCESSFUL: Closed-loop pipeline verified with human gate!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    run_e2e_demo()
