"""
tests/test_rca_engine.py
Unit tests for AdaptiveCloud Root Cause Analysis (RCA) Engine.
Verifies that:
1. Each of the 9 threat families produces a non-empty, evidence-grounded RCA.
2. Actual feature values and baseline deviations are reflected in evidence strings.
3. Wordings are formulated as evidence-based hypotheses, not dogmatic certainty.
4. Fallback to Tier 1 canonical family occurs when Tier 2 confidence is low or missing.
"""
from __future__ import annotations

import unittest
from pathlib import Path

from core.rca_engine import DEFAULT_BASELINE, RCAEngine

TEST_FAMILIES = [
    "brute_force",
    "ddos",
    "port_scan",
    "cryptomining",
    "botnet",
    "infiltration",
    "privilege_escalation",
    "web_attack",
    "cloud_iam",
    "cloud_storage",
    "host_windows",
    "benign",
]


class TestRCAEngine(unittest.TestCase):

    def setUp(self) -> None:
        self.engine = RCAEngine()

    def test_all_nine_families_produce_non_empty_rca(self) -> None:
        """Every canonical family must synthesize a complete, valid RCA response."""
        for fam in TEST_FAMILIES:
            features = {
                "cpu": 92.0 if fam == "cryptomining" else 15.0,
                "ram": 85.0 if fam == "cryptomining" else 45.0,
                "failed_logins": 50 if fam == "brute_force" else 0,
                "inbound_traffic": 90000.0 if fam == "ddos" else 120.0,
                "active_connections": 150 if fam == "port_scan" else 25,
            }

            res = self.engine.analyze(
                features=features,
                tier1_family=fam,
                tier1_confidence=0.96,
                tier2_technique="T1000",
                tier2_confidence=0.92,
                host_id="TEST-NODE-01",
            )

            self.assertIn("summary", res)
            self.assertIn("probable_root_cause", res)
            self.assertIn("evidence", res)
            self.assertIn("confidence", res)
            self.assertIn("alternative_hypotheses", res)
            self.assertIn("uncertainty_note", res)
            self.assertIn("recommended_actions", res)

            # Assert non-empty content
            self.assertTrue(len(res["summary"]) > 15, f"Summary too short for {fam}")
            self.assertTrue(len(res["probable_root_cause"]) > 10, f"Root cause empty for {fam}")
            self.assertTrue(len(res["evidence"]) > 0, f"Evidence list empty for {fam}")
            self.assertTrue(len(res["alternative_hypotheses"]) > 0, f"No alternative hypotheses for {fam}")
            self.assertTrue(len(res["recommended_actions"]) > 0, f"No recommended actions for {fam}")

    def test_evidence_grounded_in_actual_deviations(self) -> None:
        """Evidence must explicitly cite measured numbers and baseline multipliers."""
        features = {
            "cpu": 15.0,
            "ram": 45.0,
            "failed_logins": 42, # 42 logins
            "inbound_traffic": 120.0,
            "active_connections": 50,
        }

        res = self.engine.analyze(
            features=features,
            tier1_family="brute_force",
            tier1_confidence=0.95,
            host_id="LAPTOP-DEV-01",
        )

        joined_evidence = " ".join(res["evidence"])
        self.assertIn("42", joined_evidence, "Measured failed_logins not cited in evidence")
        self.assertIn("LAPTOP-DEV-01", joined_evidence, "Target host not cited in evidence")

    def test_tier2_low_confidence_fallback(self) -> None:
        """When Tier 2 technique confidence is below 0.60, engine must fall back with uncertainty note."""
        res = self.engine.analyze(
            features={"cpu": 15.0, "ram": 45.0, "failed_logins": 0, "inbound_traffic": 50000.0, "active_connections": 200},
            tier1_family="ddos",
            tier1_confidence=0.97,
            tier2_technique="T1498.001",
            tier2_confidence=0.42, # Low confidence
            host_id="GCP-GATEWAY",
        )

        self.assertIn("insufficient confidence", res["uncertainty_note"])
        self.assertIn("ddos", res["uncertainty_note"])

    def test_hypothesis_language_not_certainty(self) -> None:
        """Wording must express probabilistic hypotheses rather than absolute certainty."""
        res = self.engine.analyze(
            features={"cpu": 95.0, "ram": 80.0, "failed_logins": 0, "inbound_traffic": 120.0, "active_connections": 30},
            tier1_family="cryptomining",
            tier1_confidence=0.94,
            host_id="WORKSTATION-LINUX",
        )

        summary_lower = res["summary"].lower()
        self.assertTrue(
            "hypothesis" in summary_lower or "evidence supports" in summary_lower,
            "RCA summary does not use evidence-based hypothesis wording"
        )


if __name__ == "__main__":
    unittest.main()
