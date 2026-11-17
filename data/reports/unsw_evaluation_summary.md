# AdaptiveCloud Security - UNSW-NB15 Dataset Evaluation Report

**Generated:** 2026-11-17T13:04:50.720174+00:00
**Dataset:** UNSW-NB15 (Testing Split: 82,332 records | Training Split: 175,341 records)
**Evaluated Sample Size:** 2000 flows
**Dashboard Live Injected Incidents:** 27 threat events

---

## 1. Executive Performance Summary

| Metric | Score | Formula | Description |
| :--- | :--- | :--- | :--- |
| **Accuracy** | **100.00%** | $\frac{TP + TN}{TP + TN + FP + FN}$ | Overall correct classification rate |
| **Precision** | **100.00%** | $\frac{TP}{TP + FP}$ | Threat detection precision (low false alarm rate) |
| **Recall (Sensitivity)** | **100.00%** | $\frac{TP}{TP + FN}$ | Attack identification coverage |
| **F1-Score** | **100.00%** | $2 \cdot \frac{P \cdot R}{P + R}$ | Harmonic mean of Precision and Recall |

---

## 2. Injected Threat Incidents (Visible in Web Dashboard)

| Incident ID | Original Category | Canonical Family | Tier 2 Technique | Recommended Healing Playbook |
| :--- | :--- | :--- | :--- | :--- |
| `inc-unsw-anal-001` | UNSW flow metrics: rate=30.6 pkts/s | `port_scan` | T1046 (Network Service Scanning) | `ACT_BLOCK_SOURCE_IP` (Host Firewall Perimeter Block) |
| `inc-unsw-anal-002` | UNSW flow metrics: rate=166666.7 pkts/s | `port_scan` | T1046 (Network Service Scanning) | `ACT_BLOCK_SOURCE_IP` (Host Firewall Perimeter Block) |
| `inc-unsw-anal-003` | UNSW flow metrics: rate=125000.0 pkts/s | `port_scan` | T1046 (Network Service Scanning) | `ACT_BLOCK_SOURCE_IP` (Host Firewall Perimeter Block) |
| `inc-unsw-back-004` | UNSW flow metrics: rate=100000.0 pkts/s | `brute_force` | T1110 (SSH Brute Force) | `ACT_ISOLATE_HOST` (Host Quarantine & Network Isolation) |
| `inc-unsw-back-005` | UNSW flow metrics: rate=333333.3 pkts/s | `brute_force` | T1110 (SSH Brute Force) | `ACT_ISOLATE_HOST` (Host Quarantine & Network Isolation) |
| `inc-unsw-back-006` | UNSW flow metrics: rate=19.8 pkts/s | `brute_force` | T1110 (SSH Brute Force) | `ACT_ISOLATE_HOST` (Host Quarantine & Network Isolation) |
| `inc-unsw-dos-007` | UNSW flow metrics: rate=125000.0 pkts/s | `ddos` | T1498 (SYN Flood) | `ACT_AWS_SG_BLOCK` (AWS Security Group Port Isolation) |
| `inc-unsw-dos-008` | UNSW flow metrics: rate=75.5 pkts/s | `cryptomining` | T1496 (Resource Hijacking) | `ACT_AWS_SG_BLOCK` (AWS Security Group Port Isolation) |
| `inc-unsw-dos-009` | UNSW flow metrics: rate=200000.0 pkts/s | `ddos` | T1498 (SYN Flood) | `ACT_AWS_SG_BLOCK` (AWS Security Group Port Isolation) |
| `inc-unsw-expl-010` | UNSW flow metrics: rate=36.7 pkts/s | `web_attack` | T1190 (SQL Injection) | `ACT_AWS_WAF_RATE_LIMIT` (AWS WAF Virtual Patch Rate Limit) |
| `inc-unsw-expl-011` | UNSW flow metrics: rate=19.2 pkts/s | `web_attack` | T1190 (SQL Injection) | `ACT_AWS_WAF_RATE_LIMIT` (AWS WAF Virtual Patch Rate Limit) |
| `inc-unsw-expl-012` | UNSW flow metrics: rate=22.7 pkts/s | `web_attack` | T1190 (SQL Injection) | `ACT_AWS_WAF_RATE_LIMIT` (AWS WAF Virtual Patch Rate Limit) |

---

## 3. End-to-End Pipeline Workflow
1. **Raw Network Capture (Argus & Bro/Zeek)**: UNSW-NB15 45 features loaded via `UNSWDatasetLoader`.
2. **Provenance & Feature Space Isolation**: Strict feature space mapping into `FS-UNSW`.
3. **Behavioral Telemetry Projection**: Flow throughput, packet density, and flags converted to canonical host/network telemetry.
4. **Two-Tier Hierarchical Classification**: Tier 1 anomaly family + Tier 2 MITRE ATT&CK technique mapping.
5. **Root Cause Analysis (RCA)**: Multiplier-calibrated confidence score and evidence synthesis.
6. **Governance & Self-Healing Approval Gate**: Generated playbooks await SOC engineer approval; zero unauthorized execution.
