# AdaptiveCloud: Autonomous Self-Healing Cloud & Infrastructure Resilience Platform

[![AWS Infrastructure](https://img.shields.io/badge/AWS%20EC2-ap--south--1%20Mumbai-FF9900?logo=amazon-aws&logoColor=white)](https://aws.amazon.com/)
[![React 18](https://img.shields.io/badge/React-18%20%2B%20TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Python-3.11%20%7C%20FastAPI-009688?logo=python&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vite](https://img.shields.io/badge/Vite-6.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK%20Aligned-red)](https://attack.mitre.org/)

An enterprise-grade, full-stack autonomous cloud cybersecurity, root cause analysis (RCA), and predictive hardware failure platform. Built for distributed cloud infrastructure, hybrid data centers, and multi-tenant cloud workloads.

---

## 🌟 Key Highlights & Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ADAPTIVECLOUD UNIFIED CONTROL PLANE                             │
└──────────────────────────────────────────┬─────────────────────────────────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────────────┐
         ▼                                 ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐             ┌──────────────────┐
│ Attack Detection │             │ Root Cause (RCA) │             │  Self-Healing    │
│ 2-Tier ML Models │────────────▶│ Causal Timeline  │────────────▶│ SysAdmin Runbook │
│ UNSW-NB15 Flow   │             │ Multi-Deviations │             │ Instant AutoHeal │
└──────────────────┘             └──────────────────┘             └──────────────────┘
         │                                                                   ▲
         │                       ┌──────────────────┐                        │
         └──────────────────────▶│ Predictive Maint │────────────────────────┘
                                 │ Theil-Sen Slopes │ (Correlates Cyber Strain
                                 │ Fail Probability │  with Hardware Degradation)
                                 └──────────────────┘
```

---

## 🚀 The 4 Core Pillars

### 1. 🛡️ Attack Detection (`/`)
* **Two-Tier Classifier Engine:**
  * **Tier 1 (Canonical Family):** Classifies network flow and OS telemetry into families: `DDoS`, `Brute Force`, `Cryptomining`, `Port Scan`, `Privilege Escalation`, `Web Exploit`.
  * **Tier 2 (Technique Granularity):** Identifies specific MITRE ATT&CK technique IDs (e.g., `T1498 SYN Flood`, `T1110 SSH Spray`, `T1496 Resource Hijacking`).
* **Live Fleet Overview:** Displays real-time status across physical laptops and cloud instances.
* **On-Demand Anomaly Injection:** Inject volumetric DDoS floods, cryptomining daemons, and SSH sprays on live cloud nodes to demonstrate real-time response.

### 2. 🔍 Root Cause Analysis (RCA) (`/rca`)
* **Identified Primary Root Cause:** Definitive diagnosis of root causes (e.g., ingress gateway packet surges, unauthorized stratum miner processes).
* **Research-Grounded Causal Timeline:** Step-by-step millisecond timeline ($T+00.0\text{s} \rightarrow T+03.9\text{s}$) demonstrating attack propagation from ingress boundary through socket exhaustion to SoftIRQ kernel starvation.
* **Multi-Factor Telemetry Deviations:** Quantitative evaluation comparing live measurements ($measured$) against normal baselines ($\sigma$ deviations).
* **Differential Diagnosis:** False-positive checking against organic traffic spikes and backup jobs.

### 3. ⚡ Autonomous Self-Healing (`/healing`)
* **Zero-Permission Bottleneck:** Autonomous remediation pipeline that acts instantly without waiting for human confirmation.
* **5-Stage Remediation Pipeline:**
  1. Telemetry Threshold Triggered
  2. Two-Tier Machine Learning Inference
  3. Edge Rate-Limit Rule Applied (AWS WAF / Perimeter Firewall)
  4. Host Socket Backlog Throttling & TCP SYN Cookie Tuning
  5. Post-Healing Health Probe Normalization
* **System Administrator Runbook:** Copyable, production-ready CLI commands (`aws wafv2`, `iptables`, `sysctl`, `systemctl`, `curl`) for complete transparency.

### 4. 📈 Predictive Maintenance (`/maintenance`)
* **Theil-Sen Robust Regression:** Calculates median pairwise trend slopes on live CPU, memory, and disk telemetry to eliminate false alarms from transient noise.
* **Composite Failure Risk:** Multi-variate mathematical scoring ($0\text{--}100\%$) indicating hardware failure probability.
* **Estimated Time-to-Failure (TTF):** Quantifies time before kernel memory exhaustion (OOM) or storage saturation.

---

## 🖥️ Node Intelligence Dossier (Interactive Modal)

Clicking on **any node** across the fleet opens a comprehensive **Node Intelligence Dossier**:
* **Live Telemetry Gauges:** vCPU load, memory allocation, disk I/O, failure risk.
* **4-Tab Mission Control:** Switch between Attack Detection, RCA Forensic Dossier, Self-Healing Runbook, and Predictive Maintenance for that individual machine.
* **Per-Node Actions:** Trigger live anomalies and execute instant auto-healing directly on that instance.

---

## ☁️ AWS Cloud Fleet Integration

The system natively connects to Amazon Web Services (AWS) in the **`ap-south-1` (Mumbai, India)** region:

| Node Name | AWS Region & AZ | Public IP | Instance ID | Type | Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AWS EC2 Worker 01** | `ap-south-1b` (Mumbai) | `3.108.250.115` | `i-017c3c1add524779c` | `t2.micro` | Primary live attack target & autonomous healing host |
| **AWS EC2 Worker 02** | `ap-south-1a` (Mumbai) | `13.233.142.76` | `i-0ab2c3d4e5f678901` | `t2.micro` | Secondary high-availability multi-AZ standby node |

---

## 🛠️ Tech Stack

* **Frontend:** React 18, TypeScript, Tailwind CSS, Lucide Icons, Recharts, TanStack Query
* **Backend:** Python 3.11+, FastAPI / Python BaseHTTP, Boto3 (AWS SDK), psutil, SQLite
* **Machine Learning:** Random Forest, XGBoost, UNSW-NB15 Network Intrusion Dataset
* **Cloud Infrastructure:** AWS EC2, Amazon Linux 2023, AWS CloudWatch, AWS WAFv2

---

## 🏁 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/0mhwk/adaptive-cloud-.git
cd adaptive-cloud-
```

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=ap-south-1
```

### 3. Launch Backend Telemetry Hub
```powershell
python agent/simulate_all_laptops.py
```
*Telemetry Hub runs on `http://localhost:8001/`*

### 4. Launch Frontend Dashboard
```powershell
cd frontend
npm install
npm run dev
```
*Dashboard opens at `http://localhost:5173/`*

---

## 🧪 Running Unit Tests

```powershell
python -m unittest tests/test_rca_engine.py
python -m unittest tests/test_permission_gate.py
```

---

## 👤 Author & Profile

* **GitHub:** [@0mhwk](https://github.com/0mhwk)
* **Project Repository:** [adaptive-cloud-](https://github.com/0mhwk/adaptive-cloud-)
