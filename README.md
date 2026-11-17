# AI-Based Adaptive Cloud Security & Predictive Maintenance System

> **Budget: ₹0 | Cloud: GCP Free Trial | Dev: Windows 10/11 + Docker Desktop (WSL2 backend)**

A production-style, full-stack AI security monitoring and autonomous self-healing platform that:
- Collects real-time telemetry from **Windows Server 2022 GCP VMs** and **4 Physical Laptops** using `psutil` + `pywin32`
- Runs hierarchical **Tier 1 (9 Canonical Families)** and **Tier 2 (MITRE ATT&CK techniques)** classification on 5-feature behavioral vectors
- Synthesizes evidence-grounded **Root Cause Analysis (RCA)** from actual feature deviations against baseline
- Enforces a strict **Human Approval Gate**: Zero disruptive playbooks execute without explicit operator authorization
- Executes scoped countermeasures under **dry-run** by default, verifies recovery via live telemetry probes, and provides **1-click rollback**
- Visualises everything in an OLED Pure Black **React 18 + TypeScript + Tailwind** dashboard

---

## Autonomous Self-Healing Pipeline with Human Approval

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           ADAPTIVECLOUD CLOSED-LOOP GOVERNANCE PIPELINE                               │
└───────────────────────────────────────────────────────────────────────────────────────────────────────┘

 [1. Ingest Telemetry] ────▶ [2. Tier 1 & 2 Classify] ────▶ [3. Synthesize RCA & Propose Healing Plan]
  (psutil / GCP VPC)           (9 Families & MITRE)           (Feature Baseline Multiplier Deviations)
                                                                             │
                                                                             ▼
 [6. Verify Probe] ◀──── [5. Execute Playbook] ◀──── [4. ASK OPERATOR PERMISSION (Human Gate)]
  (Pre vs Post Probe)     (Dry-run / Live Scoped)      (Approve Selected | Reject | Expire Timeout)
         │                                                           │
         ▼                                                           ▼
 [7. Commit Immutable Audit] ────────────────────────────────▶ [8. React 18 Dashboard & 1-Click Rollback]
```

### Pipeline Comparison:
- **Legacy Pipeline:** `Classify -> Check Safety -> Respond -> Verify -> Record -> Show`
- **New Governance Pipeline:** `Classify -> Build Incident + RCA -> Propose Healing Plan -> Check Safety -> ASK PERMISSION -> (Approved) Execute -> Verify -> Record -> Show`

---

## 9 Canonical Threat Families Supported

| Canonical Family | Primary Signals | Typical Root Cause | Scoped Healing Playbook |
| :--- | :--- | :--- | :--- |
| **`brute_force`** | `failed_logins`, `active_connections` | Unshielded RDP/SSH port; dictionary spray | Dynamic host firewall block rule (`netsh`) |
| **`ddos`** | `inbound_traffic` (>1000 pps), `cpu` | Ingress volumetric flood; reflection botnet | Google Cloud Armor edge rate-limiting policy |
| **`port_scan`** | `active_connections`, `inbound_traffic` | Adversary perimeter SYN sweep | Host firewall drop rule & stealth mode |
| **`cryptomining`** | `cpu` (>85%), `ram` | Unauthorized miner daemon (XMRig) | Kill process (`kill -9`) & isolate binary to quarantine |
| **`privilege_escalation`** | `cpu`, abnormal tokens | LSASS memory dump / token abuse | Terminate injector process & purge Kerberos tickets |
| **`web_attack`** | `inbound_traffic`, `active_connections` | SQLi / SSRF against cloud metadata | WAF rule deployment & client session invalidation |
| **`cloud_iam`** | `active_connections`, IAM audit logs | Leaked service account key | Revoke compromised SA key via `gcloud iam` |
| **`cloud_storage`** | `inbound_traffic` (egress burst) | Unauthorized bucket egress transfer | Freeze bucket egress & enforce uniform bucket ACL |
| **`benign`** | All within normal bounds | Normal operational workload | Continuous baseline monitoring |

---

## How to Run Dataset Replay & Demonstrations

### 1. Run the Historical Dataset Replay
Processes `ml/data/cloud_attacks_238.csv` through Tier 1 & Tier 2 classifiers, generates RCA for all attacks, de-duplicates similar events, and exports summary reports:
```powershell
python scripts/replay_dataset.py --limit 50 --sample-per-family 5 --seed 42
```
*Outputs generated at `data/reports/dataset_replay_records.json` and `data/reports/dataset_replay_summary.csv`.*

### 2. Run the End-to-End Approval & Self-Healing Demo
Simulates a live attack, verifies that the system stops at the Permission Gate, simulates operator approval, executes a dry-run playbook, verifies normalization, and demonstrates 1-click rollback:
```powershell
python scripts/demo_self_healing_approval.py
```

### 3. Run Unit & Safety Gate Tests
```powershell
python -m unittest tests/test_rca_engine.py
python -m unittest tests/test_permission_gate.py
```

### 4. Start the Physical Hub & Dashboard
```powershell
# Terminal 1: Start Central Telemetry Hub & Permission Gate API (Port 8001)
python agent/simulate_all_laptops.py

# Terminal 2: Start React Frontend Dashboard (Port 5173)
cd frontend
npm run dev
```
Open **`http://localhost:5173/rca`** to inspect the live **Incidents & Self-Healing with Human Approval** console.

---

---

## Architecture

```
Windows Agent (GCP VM)                  Developer PC (Windows 10/11)
┌────────────────────┐                  ┌─────────────────────────────────┐
│ psutil + pywin32   │──X-API-Key POST──▶│ Nginx :443 (TLS)                │
│ 30s snapshot loop  │  Tailscale VPN    │  → FastAPI :8000                │
│ Wazuh Agent MSI    │──────────────────▶│  → ML Service :8001             │
└────────────────────┘                  │  → PostgreSQL 16                │
                                        │  → React SPA (dist/)            │
                                        └─────────────────────────────────┘
                                                     │ WebSocket
                                              Browser dashboard
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Agent (Windows) | Python 3.11, psutil, pywin32, tenacity |
| Backend | FastAPI, SQLAlchemy 2 async, Alembic, asyncpg |
| Database | PostgreSQL 16 (partitioned `metrics` table) |
| ML | XGBoost, scikit-learn, pandas, numpy, joblib |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, Zustand |
| Auth | JWT (users) + X-API-Key bcrypt (agents) |
| Proxy | Nginx 1.27 (TLS termination, WebSocket upgrade) |
| Network | Tailscale (WireGuard mesh, free tier) |
| Containers | Docker Compose (Linux containers on WSL2 backend) |

---

## Prerequisites

- Windows 10/11 with PowerShell 7+
- Docker Desktop (WSL2 backend) — [install](https://docs.docker.com/desktop/install/windows-install/)
- Python 3.11+ — [install](https://www.python.org/downloads/)
- Node 20+ — [install](https://nodejs.org/)
- Git — [install](https://git-scm.com/)
- Tailscale (free) — [install](https://tailscale.com/download/windows)

---

## Quick Start

### 1. Bootstrap
```powershell
cd d:\NEW_ADAPTIVECLOUD
.\scripts\bootstrap.ps1
```

### 2. Configure secrets
```powershell
# Edit the copied .env files
code backend\.env     # Set JWT_SECRET_KEY (32-char hex)
code agent\.env       # Set AGENT_ID, AGENT_API_KEY, BACKEND_URL
```

### 3. Generate TLS certificate
```powershell
.\scripts\generate-cert.ps1
```

### 4. Start the Docker stack
```powershell
cd deploy
docker compose up -d
docker compose logs -f backend   # Watch startup
```

### 5. Run database migrations
```powershell
cd ..\backend
.\.venv\Scripts\alembic upgrade head
```

### 6. Create the first admin user
```powershell
.\.venv\Scripts\python scripts\create_admin.py
```

### 7. Register a monitoring agent (admin API)
```powershell
# Replace <token> with your login token from POST /api/v1/auth/login
Invoke-RestMethod -Method POST -Uri "https://localhost/api/v1/agents" `
  -Headers @{ Authorization = "Bearer <token>" } `
  -ContentType "application/json" `
  -Body '{"hostname":"WIN-SRV-01","os_version":"Windows Server 2022","ip_address":"100.64.x.x"}'
# Save the returned api_key — it is shown ONCE
```

### 8. Start the frontend dev server
```powershell
cd ..\frontend
npm run dev
# Open https://localhost:5173
```

### 9. Install agent on a GCP Windows VM
```powershell
# On the GCP VM (after Tailscale + Python installed):
cd C:\adaptive-agent
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
# Edit .env with your AGENT_ID, AGENT_API_KEY, BACKEND_URL
.\.venv\Scripts\python src\main.py
```

---

## Directory Structure

```
NEW_ADAPTIVECLOUD/
├── agent/                  # Windows monitoring agent
│   ├── src/
│   │   ├── collector.py    # psutil + pywin32 telemetry
│   │   ├── sender.py       # HTTP POST with retry
│   │   └── main.py         # Entry point
│   └── requirements.txt
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/v1/routes/  # auth, agents, ingest, metrics, predictions
│   │   ├── core/           # config, security, logging
│   │   ├── db/             # SQLAlchemy engine + base
│   │   ├── models/         # ORM models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── websocket/      # WS manager + router
│   ├── alembic/            # DB migrations
│   └── scripts/            # create_admin.py
├── ml/                     # ML microservice
│   └── src/
│       ├── features.py     # Feature extraction
│       ├── trainer.py      # XGBoost training pipeline
│       ├── predictor.py    # Inference
│       └── app.py          # FastAPI ML service
├── frontend/               # React 18 dashboard
│   └── src/
│       ├── pages/          # LoginPage, DashboardPage
│       ├── components/     # MetricCard, LiveAlertBanner, MetricChart
│       ├── hooks/          # useWebSocket
│       ├── store/          # authStore (Zustand)
│       ├── api/            # axios client with auto-refresh
│       └── types/          # TypeScript type definitions
├── deploy/                 # Docker Compose + Nginx + certs
│   ├── docker-compose.yml
│   └── nginx/
├── docs/                   # API_CONTRACT.md, DATA_SCHEMA.md, ARCHITECTURE.md
└── scripts/                # bootstrap.ps1, generate-cert.ps1
```

---

## API Quick Reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/v1/auth/login | — | Get JWT tokens |
| POST | /api/v1/auth/refresh | — | Refresh access token |
| GET | /api/v1/agents | admin | List agents |
| POST | /api/v1/agents | admin | Register agent (returns api_key once) |
| POST | /api/v1/ingest | X-API-Key | Ingest metric snapshot |
| GET | /api/v1/metrics | analyst+ | Query metrics |
| GET | /api/v1/predictions | analyst+ | Query predictions |
| GET | /api/v1/ml/status | analyst+ | Model status |
| POST | /api/v1/ml/train | admin | Trigger retraining |
| GET | /api/v1/health | public | Healthcheck |
| WS | /ws/live?token=... | JWT | Live event stream |

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for full schemas.

---

## Contributing

1. Keep all scripts as PowerShell (`.ps1`) or cross-platform Python
2. Never commit `.env` files or certificates
3. No hardcoded metrics — if no model: `{"status":"not_available"}`
4. UTC timestamps everywhere, UUID v4 IDs
5. Update `docs/DATA_SCHEMA.md` before changing any shared data contract

---

## Licence

MIT

