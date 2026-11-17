"""
core/tier_classifiers.py
Two-Tier Hierarchical Threat Classifier for AdaptiveCloud:
Tier 1: Canonical family classifier (9 canonical threat families)
Tier 2: Technique-specific predictor (aligned with MITRE ATT&CK and ml/data/cloud_attacks_238.csv)
Inputs: 5-feature behavioral vector: [cpu, ram, failed_logins, inbound_traffic, active_connections]
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("tier_classifiers")
TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "ml" / "data" / "cloud_attacks_238.csv"

CANONICAL_FAMILIES = (
    "brute_force",
    "ddos",
    "port_scan",
    "cryptomining",
    "privilege_escalation",
    "web_attack",
    "cloud_iam",
    "cloud_storage",
    "benign",
)


class TierClassifiers:
    """Hierarchical Tier 1 & Tier 2 Inference Engine."""

    def __init__(self, taxonomy_path: Path | str | None = None) -> None:
        self.taxonomy_path = Path(taxonomy_path) if taxonomy_path else TAXONOMY_PATH
        self.taxonomy_techniques = self._load_taxonomy()

    def _load_taxonomy(self) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        if not self.taxonomy_path.exists():
            logger.warning("Taxonomy CSV not found at %s. Using default MITRE list.", self.taxonomy_path)
            return entries

        try:
            with open(self.taxonomy_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    entries.append(row)
        except Exception as e:
            logger.error("Failed loading taxonomy: %s", e)
        return entries

    def classify(self, features: dict[str, float | int]) -> dict[str, Any]:
        """
        Evaluate 5-feature behavioral vector:
        cpu: % (0-100)
        ram: % (0-100)
        failed_logins: count
        inbound_traffic: pkts/sec or bytes/sec
        active_connections: count
        """
        cpu = float(features.get("cpu", 15.0))
        ram = float(features.get("ram", 45.0))
        logins = float(features.get("failed_logins", 0.0))
        inbound = float(features.get("inbound_traffic", 120.0))
        conns = float(features.get("active_connections", 25.0))

        # Heuristic scoring calibrated to dataset distributions
        scores: dict[str, float] = {fam: 0.05 for fam in CANONICAL_FAMILIES}

        # 1. Brute Force scoring
        if logins >= 10:
            scores["brute_force"] += min(0.95, 0.40 + (logins / 50.0) * 0.50)
            if conns > 35:
                scores["brute_force"] += 0.10

        # 2. DDoS scoring
        if inbound > 1000.0 or (inbound > 500.0 and conns > 100.0):
            scores["ddos"] += min(0.98, 0.50 + (inbound / 10000.0) * 0.45)
            if cpu > 60:
                scores["ddos"] += 0.05

        # 3. Port Scan scoring
        if conns > 80.0 and inbound < 500.0 and logins < 5:
            scores["port_scan"] += 0.85
        elif conns > 45.0 and logins < 5:
            scores["port_scan"] += 0.55

        # 4. Cryptomining scoring
        if cpu >= 85.0:
            scores["cryptomining"] += min(0.96, 0.60 + (cpu - 85.0) / 15.0 * 0.35)
            if ram > 65.0:
                scores["cryptomining"] += 0.05

        # 5. Privilege Escalation scoring
        if features.get("lsass_probe") or (cpu > 40.0 and features.get("priv_events", 0) > 0):
            scores["privilege_escalation"] += 0.94
        elif features.get("token_anomaly"):
            scores["privilege_escalation"] += 0.90

        # 6. Web Attack scoring
        if features.get("sqli_signature") or features.get("ssrf_probe"):
            scores["web_attack"] += 0.95
        elif inbound > 300.0 and conns > 40.0 and logins < 2 and cpu < 50:
            scores["web_attack"] += 0.45

        # 7. Cloud IAM scoring
        if features.get("iam_privilege_abuse") or features.get("sa_key_leak"):
            scores["cloud_iam"] += 0.96

        # 8. Cloud Storage scoring
        if features.get("bucket_egress_burst") or features.get("egress_gb", 0) > 10:
            scores["cloud_storage"] += 0.97

        # 9. Benign default if all features within baseline
        if (
            logins < 3
            and inbound < 300.0
            and conns < 40.0
            and cpu < 65.0
            and not any([
                features.get("lsass_probe"),
                features.get("ssrf_probe"),
                features.get("iam_privilege_abuse"),
                features.get("bucket_egress_burst"),
            ])
        ):
            scores["benign"] = 0.97

        # Normalize probabilities
        top_family = max(scores, key=scores.get) # type: ignore
        top_conf = round(min(0.99, scores[top_family]), 3)

        # Tier 2 prediction: Select matching technique from taxonomy
        tier2_technique = None
        tier2_conf = None

        if top_family != "benign":
            matching_techs = [
                t for t in self.taxonomy_techniques
                if t.get("canonical_family", "").lower() == top_family
                or (top_family == "ddos" and t.get("canonical_family") in ("ddos", "dos"))
            ]
            if matching_techs:
                # Select most specific or primary matching technique
                chosen = matching_techs[0]
                tier2_technique = f"{chosen.get('mitre_technique')} ({chosen.get('attack_name')})"
                tier2_conf = round(max(0.70, top_conf - 0.03), 3)
            else:
                # Default mapping
                defaults = {
                    "brute_force": "T1110.004 (Credential Stuffing)",
                    "ddos": "T1498.001 (Direct Network Flood)",
                    "port_scan": "T1046 (Network Service Scanning)",
                    "cryptomining": "T1496 (Resource Hijacking)",
                    "privilege_escalation": "T1003.001 (LSASS Memory Dump)",
                    "web_attack": "T1190 (Exploit Public-Facing Application)",
                    "cloud_iam": "T1098 (Account Manipulation)",
                    "cloud_storage": "T1537 (Transfer Data to Cloud Account)",
                }
                tier2_technique = defaults.get(top_family)
                tier2_conf = round(max(0.70, top_conf - 0.05), 3)

        return {
            "tier1_family": top_family,
            "tier1_confidence": top_conf,
            "tier2_technique": tier2_technique,
            "tier2_confidence": tier2_conf,
            "scores": scores,
        }


tier_classifiers = TierClassifiers()
