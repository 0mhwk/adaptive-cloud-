# AdaptiveCloud: An Autonomous, Self-Healing Cloud Security and Root Cause Analysis Framework with Live Google Cloud Platform Integration

**Authors:** Security Systems Research Group  
**Target Venue:** IEEE Transactions on Cloud Computing / ACM Transactions on Privacy and Security (TOPS)  
**Classification:** Cloud Security, Autonomous Self-Healing, Root Cause Analysis, Machine Learning, MITRE ATT&CK  

---

## Abstract
Modern multi-tenant cloud platforms such as Google Cloud Platform (GCP) provide native perimeter security mechanisms, including Cloud Armor, Security Command Center (SCC), and VPC Firewall Rules. However, the contemporary cloud threat landscape—characterized by high-velocity volumetric floods, evasive credential access, serverless abuse, and control-plane privilege escalation—exposes three fundamental limitations: (1) high Mean Time to Remediate (MTTR) driven by alert fatigue and disjointed telemetry pipelines; (2) lack of transparent, evidence-grounded Root Cause Analysis (RCA); and (3) rigid Security Orchestration, Automation, and Response (SOAR) playbooks that risk critical service disruption when triggered without strict scope boundaries. 

This paper presents **AdaptiveCloud**, an autonomous, evidence-driven cloud security architecture that couples real-time telemetry from live GCP production servers (Compute Engine, VPC Flow Logs, Cloud Audit Logs, and Cloud Monitoring) with a two-tier hierarchical machine learning classifier, a dynamic RCA inference engine, and a scoped self-healing executor governed by a strict human-in-the-loop permission gate. Evaluated against a comprehensive 238-attack taxonomy covering network, web, cloud control plane, and host-level vectors, AdaptiveCloud achieves sub-second inference latency, autonomous remediation dispatch in under 450ms, 99.8% traffic normalization under volumetric stress, and zero accidental disruptions to protected infrastructure via deterministic safety guardrails.

**Keywords:** Cloud Security, Autonomous Self-Healing, Google Cloud Platform (GCP), Root Cause Analysis (RCA), MITRE ATT&CK, Machine Learning, Human-in-the-Loop.

---

## 1. Introduction

Cloud computing infrastructures have evolved into complex, highly distributed environments where ephemeral microservices, identity perimeters, and multi-tenant resource hierarchies introduce unprecedented attack surfaces. While cloud service providers (CSPs) like Google Cloud operate under the Shared Responsibility Model, standard cloud security tooling remains predominantly **reactive and advisory**.

```mermaid
flowchart TD
    subgraph CSP_Blindspot["Traditional Cloud Monitoring Blind Spots"]
        A["VPC Flow Logs & Audit Telemetry"] --> B["Cloud Security Command Center / SIEM"]
        B --> C["Alert Fatigue (10,000+ alerts/day)"]
        C --> D["Manual SOC Triage (MTTR: 45 min - 4 hours)"]
        D --> E["Data Breach / Service Outage Occurs"]
    end

    subgraph AdaptiveCloud_Pipeline["AdaptiveCloud Autonomous Architecture"]
        F["Live GCP Server Telemetry"] --> G["Tier 1 & 2 Hierarchical ML Engine"]
        G --> H["Dynamic RCA Synthesizer (Quantified Deviations)"]
        H --> I["Safety Guardrail Veto & Scope Validator"]
        I --> J["Human-in-the-Loop Permission Gate"]
        J -- "Approved" --> K["GCP Cloud Armor / IAM / Host Dynamic Remediation"]
        K --> L["Closed-Loop Post-Healing Telemetry Verification (<500ms)"]
    end
```

### 1.1 Problem Statement & GCP Limitations
When monitoring live production infrastructure on Google Cloud Platform, security operators encounter critical operational gaps:
1. **The Telemetry-Action Gap:** GCP Security Command Center surfaces anomalous findings, but requires separate Cloud Functions, Pub/Sub subscriptions, and complex IAM permissions to trigger reactive countermeasures.
2. **Alert Dogmatism without Root Cause Grounding:** Traditional IDS/IPS systems trigger alerts based on signature matching without explaining *why* an anomaly departed from baseline or considering benign operational alternative hypotheses (such as marketing flash crowds or scheduled CI/CD backups).
3. **Destructive Remediation Risks:** Fully autonomous SOAR playbooks frequently cause collateral damage (e.g., locking out critical service accounts, blocking internal load balancer health checks, or killing core operating system daemons).
4. **Taxonomy Fragmentation:** Public attack datasets (CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, Mordor) classify attacks in isolated domains (network-only or host-only), lacking a unified taxonomy that bridges network flows, web exploits, cloud control plane IAM abuse, and host persistence.

### 1.2 Contributions of this Work
AdaptiveCloud addresses these challenges through the following key contributions:
- **Hierarchical Two-Tier Threat Inference:** A dual-stage classification engine mapping a 5-feature behavioral telemetry vector to canonical threat families (Tier 1) and specific MITRE ATT&CK techniques (Tier 2) across a 238-attack taxonomy.
- **Evidence-Grounded RCA Synthesizer:** An analytical engine that evaluates observed telemetry against dynamic operational baselines ($\Delta F_i = F_{\text{measured}} / F_{\text{baseline}}$), generates testable hypotheses, cites correlated forensic evidence, and documents alternative benign explanations.
- **Closed-Loop Scoped Self-Healing with Safety Guardrails:** A registry of playbooks enforcing strict scope validation, safety veto checks (protecting hub hosts, critical IPs, and OS system processes), dry-run pre-execution, and deterministic rollback functions.
- **Human-in-the-Loop Permission Gate:** An interactive governance model ensuring that destructive actions on production GCP servers require explicit operator sign-off while non-destructive isolations execute safely in simulated dry-run mode.
- **Live GCP Integration Architecture:** Seamless ingestion of GCP Compute Engine metrics, VPC Flow Logs, Cloud Audit Logs, and edge enforcement via Google Cloud Armor and Cloud IAM APIs.

---

## 2. Related Work and State-of-the-Art Comparison

Table 1 positions AdaptiveCloud against existing commercial and academic cloud security frameworks.

### Table 1: State-of-the-Art Comparison Matrix

| Feature / Capability | Google Cloud Armor + SCC | AWS GuardDuty + Detective | Traditional SOAR (Cortex / Splunk) | Suricata / Snort IDS | **AdaptiveCloud (This Project)** |
|---|---|---|---|---|---|
| **Monitoring Source** | GCP VPC Logs / Audit | CloudTrail / VPC Flow | Syslog / API Connectors | Network Packet Capture | **Hybrid: GCP Cloud + Live OS Endpoints** |
| **Taxonomy Breadth** | Cloud-native findings | AWS-specific events | Vendor-dependent rules | Flow-based signatures | **238 Multi-Domain Attack Taxonomy** |
| **Root Cause Analysis** | Static advisory text | Entity graph link | Manual investigation | None (Rule ID only) | **Dynamic Baseline Deviation & Hypothesis Engine** |
| **Alternative Hypotheses** | No | No | No | No | **Yes (Considers benign IT/DevOps tasks)** |
| **Self-Healing Automation** | Manual / Scripted | EventBridge rules | Fragile custom playbooks | Drop packet only | **Deterministic Scoped Playbooks with Rollback** |
| **Safety Guardrails** | IAM-dependent | Role policies | Custom scripts | None | **Built-in Protected Host/Process Veto Engine** |
| **Governance Model** | Post-incident alert | Post-incident alert | Unchecked automation | Inline block | **Human-in-the-Loop Permission Gate** |
| **Verification Probe** | No | No | External monitoring | No | **Closed-Loop Pre/Post Telemetry Verification** |

---

## 3. System Architecture & Live GCP Server Integration

AdaptiveCloud operates as a distributed, multi-layer security controller interfacing directly with Google Cloud Platform services and hybrid endpoint agents.

```mermaid
sequenceDiagram
    autonumber
    participant Attacker as Adversary / Scanner
    participant GCP_Edge as GCP Cloud Armor & VPC
    participant VM as GCP Compute Engine (Live Server)
    participant Engine as AdaptiveCloud Inference & RCA Engine
    participant Gate as Human Permission Gate (Dashboard)
    participant Operator as SOC Security Engineer

    Attacker->>GCP_Edge: Volumetric Flood / SQLi / SSH Brute Force
    GCP_Edge->>VM: Ingress Packets assault host buffers
    VM->>Engine: Stream 5-Feature Telemetry Vector [cpu, ram, logins, inbound, conns]
    Engine->>Engine: Tier 1 Family & Tier 2 MITRE Technique Classification
    Engine->>Engine: Compute Baseline Multipliers (Delta = Measured / Baseline)
    Engine->>Engine: Synthesize Evidence-Grounded RCA & Alternative Hypotheses
    Engine->>Engine: Validate Safety Guardrails (Check protected IPs/PIDs)
    Engine->>Gate: Create Incident Record (Status: Awaiting Approval)
    Gate->>Operator: Alert UI Drawer with Probable Cause & Proposed Playbook
    Operator->>Gate: Click [Approve] (Digital Signature & Execution Grant)
    Gate->>GCP_Edge: Dispatch Cloud Armor Edge Ban Rule (API 1000)
    Gate->>VM: Dispatch Host Inbound Firewall Block (netsh / iptables)
    GCP_Edge-->>Attacker: Ingress Packets Dropped at Global Edge POPs
    VM->>Engine: Post-Healing Telemetry Watchdog Probe (Inbound drops 99.8%)
    Engine->>Gate: Transition Status to "Verified Healed" & Commit to Audit DB
```

### 3.1 Live GCP Server Integration Workflow
1. **Telemetry Ingestion Layer:**
   - **GCP Compute Engine (GCE) Agent:** A lightweight psutil daemon running on monitored Linux/Windows cloud instances streaming the 5-feature behavioral vector: CPU utilization ($\%$), RAM usage ($\%$), Failed Authentication bursts ($\text{count}$), Inbound network traffic ($\text{pkts/sec}$), and Active TCP socket count.
   - **GCP VPC Flow Logs:** Captures aggregate IP 5-tuples, packet volume, and TCP flags across subnets.
   - **GCP Cloud Audit Logs:** Real-time administrative activity stream capturing `SetIamPolicy`, `CreateServiceAccountKey`, and storage bucket metadata changes.
2. **Inference & Analytical Core:**
   - Evaluates real-time telemetry against normal operational distributions calibrated to baseline bounds ($B_{\text{cpu}} = 15\%$, $B_{\text{ram}} = 45\%$, $B_{\text{logins}} = 0$, $B_{\text{traffic}} = 120\text{ pps}$, $B_{\text{conns}} = 25$).
   - Derives relative anomaly multipliers ($\Delta F_i$) to distinguish localized process spikes from distributed edge saturation.
3. **Safety Guardrail Engine:**
   - Prior to proposing any countermeasure, the safety engine validates target resources against immutable allowlists:
     $$\text{Target} \notin \mathcal{P}_{\text{hosts}} \cup \mathcal{P}_{\text{IPs}} \cup \mathcal{P}_{\text{processes}}$$
   - Prevents blocking localhost (`127.0.0.1`), CGNAT interfaces, cluster hub addresses, or terminating system-critical operating system daemons (`systemd`, `init`, `csrss.exe`, `lsass.exe`, `sshd`).
4. **Remediation & Closed-Loop Verification:**
   - Upon operator authorization via the frontend dashboard, the designated playbook executes.
   - A dedicated verification watchdog probes the target layer at $t = t_{\text{exec}} + 300\text{ms}$ to confirm telemetry normalization. If abnormal metrics persist, the operator is alerted to escalate.

---

## 4. Mathematical Formulation & Detection Modeling

### 4.1 Behavioral Feature Vector Representation
Each monitored host or cloud asset $\mathcal{A}_k$ is modeled at sampling epoch $t$ by a continuous state vector $\mathbf{x}_t \in \mathbb{R}^5$:
$$\mathbf{x}_t = \begin{bmatrix} f_{\text{cpu}}(t) & f_{\text{ram}}(t) & f_{\text{logins}}(t) & f_{\text{inbound}}(t) & f_{\text{conns}}(t) \end{bmatrix}^T$$

### 4.2 Quantified Baseline Deviation Matrix
Let $\mathbf{b} = \begin{bmatrix} b_{\text{cpu}} & b_{\text{ram}} & b_{\text{logins}} & b_{\text{inbound}} & b_{\text{conns}} \end{bmatrix}^T$ represent the nominal baseline vector established during uncompromised operation. The relative deviation vector $\mathbf{\delta}_t = \begin{bmatrix} \delta_1 & \delta_2 & \delta_3 & \delta_4 & \delta_5 \end{bmatrix}^T$ is computed as:
$$\delta_i(t) = \begin{cases} \frac{x_{t,i}}{b_i}, & \text{if } b_i > 0 \\ x_{t,i}, & \text{if } b_i = 0 \end{cases}$$

### 4.3 Multi-Tier Hierarchical Inference Formulation
The threat classification is solved via hierarchical decomposition:
$$\mathcal{M}(\mathbf{x}_t) = \langle \mathcal{T}_1(\mathbf{x}_t), \mathcal{T}_2(\mathbf{x}_t \mid \mathcal{T}_1) \rangle$$
Where:
- $\mathcal{T}_1(\mathbf{x}_t) \to \mathcal{C}_k \in \{\text{DoS}, \text{BruteForce}, \text{PortScan}, \text{Cryptomining}, \text{WebAttack}, \text{CloudIAM}, \text{CloudStorage}, \text{HostWindows}, \text{Infiltration}, \text{Benign}\}$
- $\mathcal{T}_2(\mathbf{x}_t \mid \mathcal{C}_k) \to \mathcal{K}_j \in \text{MITRE ATT\&CK Techniques (238 classes)}$

Confidence score calibration incorporates entropy penalization to prevent over-confident assertions on edge distributions:
$$\hat{P}(\mathcal{C}_k \mid \mathbf{x}_t) = \frac{\exp(s_k(\mathbf{x}_t) / \tau)}{\sum_{j=1}^{K} \exp(s_j(\mathbf{x}_t) / \tau)}$$
Where $\tau$ denotes the temperature scaling parameter calibrated on validation splits.

### 4.4 Mean Time to Remediate (MTTR) Formulation
The total operational remediation latency $T_{\text{remediate}}$ is modeled as the sum of sequential lifecycle phases:
$$T_{\text{remediate}} = t_{\text{detect}} + t_{\text{classify}} + t_{\text{RCA}} + t_{\text{veto}} + t_{\text{approval}} + t_{\text{dispatch}} + t_{\text{verify}}$$

In manual SOC workflows:
$$T_{\text{manual}} \approx 15\text{ min} + 30\text{ min} + 45\text{ min} + \dots \gg 2700\text{ seconds}$$
Under AdaptiveCloud with human permission gate:
$$T_{\text{AdaptiveCloud}} = 1.2\text{s} + 0.04\text{s} + 0.12\text{s} + 0.01\text{s} + t_{\text{operator\_click}} + 0.34\text{s} + 0.40\text{s} \approx 2.11\text{s} + t_{\text{operator\_click}}$$

---

## 5. The 238-Attack Taxonomy & Remediation Matrix

AdaptiveCloud categorizes the entire 238-attack taxonomy into structured operational archetypes. Table 2 provides representative empirical mappings.

### Table 2: Representative Attack Taxonomy, RCA, and Playbook Mapping

| ID | Attack Name | Category | Canonical Family | MITRE ATT&CK | Primary Telemetry Signal | Hypothesized Root Cause | Scoped Playbook ID | Remediation Action | Risk | Reversible |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | SYN Flood | DoS | `dos` | T1498 | `inbound_traffic_surge` | Ingress socket backlog exhaustion | `ACT_GCP_ARMOR_RATE_LIMIT` | Edge SYN Rate-Limit & Drop | Low | Yes |
| **8** | HTTP GET Flood | DoS | `dos` | T1499 | `inbound_traffic_surge` | Layer-7 web worker exhaustion | `ACT_GCP_ARMOR_RATE_LIMIT` | Cloud Armor L7 Rate-Based Ban | Low | Yes |
| **28** | DNS Amplification | DDoS | `ddos` | T1498 | `inbound_traffic_surge` | Open resolver reflection amplification | `ACT_GCP_ARMOR_RATE_LIMIT` | Cloud Armor Edge Reflection Ban | Low | Yes |
| **44** | SSH Brute Force | Brute Force | `brute_force` | T1110 | `failed_logins_spike` | Exposed port 22 without rate-limiting | `ACT_BLOCK_SOURCE_IP` | Dynamic Host Firewall Inbound Block | Low | Yes |
| **46** | RDP Brute Force | Brute Force | `brute_force` | T1110 | `failed_logins_spike` | Public WAN port 3389 exposure | `ACT_BLOCK_SOURCE_IP` | Firewall Block & Restrict to Tailscale | Low | Yes |
| **64** | TCP SYN Scan | Recon | `port_scan` | T1046 | `active_connections_churn` | Stealth port sweep for listening daemons | `ACT_DROP_SCANNER_IP` | Dynamic Null-Route & Stealth Mode | Low | Yes |
| **88** | SQL Injection | Web Attack | `web_attack` | T1190 | `waf_signature_match` | Unsanitized input in query parameters | `ACT_WAF_INJECT_RULE` | Cloud Armor SQLi Preconfigured Rule | Low | Yes |
| **99** | SSRF to IMDS | Web Attack | `web_attack` | T1190 | `imds_http_request` | Coerced request to 169.254.169.254 | `ACT_WAF_INJECT_RULE` | Block Metadata & Mandate IMDSv2 | Med | Yes |
| **111** | Log4Shell | Web Attack | `web_attack` | T1190 | `waf_signature_match` | JNDI lookup string in HTTP header | `ACT_WAF_INJECT_RULE` | Deploy Cloud Armor Log4Shell Rule | High | Yes |
| **126** | Mirai IoT C2 | Botnet | `botnet` | T1071 | `outbound_beacon_cadence`| Rogue binary beaconing to C2 IRC | `ACT_KILL_MINING_PROCESS` | Kill PID & Quarantine Binary | Med | No |
| **141** | XMRig Cryptominer | Botnet / Crypto | `cryptomining`| T1496 | `cpu_miner_saturation` | Unauthorized mining daemon in /tmp | `ACT_KILL_MINING_PROCESS` | Kill PID 4912 & Block Stratum Pool | Med | No |
| **145** | ARP Cache Poisoning | Infiltration | `infiltration`| T1557 | `arp_table_inconsistency`| Forged gratuitous ARP frames on LAN | `ACT_ISOLATE_NETWORK_INTERFACE` | Isolate Virtual NIC & Flush Cache | Med | Yes |
| **163** | Public Bucket Exposure | Cloud Control | `cloud_storage`| T1530 | `bulk_egress_burst` | Bucket ACL changed to allUsers read | `ACT_FREEZE_BUCKET_EGRESS` | Enforce Uniform Bucket Access | High | Yes |
| **164** | IAM Privilege Escalation| Cloud Control | `cloud_iam` | T1098 | `unauthorized_cloud_api` | Stolen SA key calling SetIamPolicy | `ACT_REVOKE_SA_KEY` | Delete SA Key via Cloud IAM API | High | No |
| **209** | Mimikatz LSASS Dump | Host Windows | `host_windows`| T1003 | `lsass_memory_read` | OpenProcess VM_READ against lsass.exe | `ACT_TERMINATE_EXPLOIT_PID`| Terminate PID & Flush Tickets | High | No |
| **226** | Ransomware Encryption | Host Windows | `host_windows`| T1486 | `cpu_saturation` | Mass document file encryption | `ACT_TERMINATE_EXPLOIT_PID`| Kill Process & Restore VSS Backup | High | No |

---

## 6. Experimental Results & Performance Evaluation

AdaptiveCloud was evaluated across two testing environments: (1) a live Google Cloud Platform deployment running four Compute Engine instances behind a Global External HTTPS Load Balancer with Cloud Armor enabled; and (2) an offline benchmark replay testbed executing all 238 attack taxonomy scenarios.

### 6.1 Detection and Classification Accuracy
- **Tier 1 Canonical Family Accuracy:** 98.4% across 10,000 synthetic and replayed flow frames.
- **Tier 2 Technique Specificity:** 94.2% top-1 accuracy when telemetry features exhibited distinct multi-variable correlation (e.g., failed logins + connection churn).
- **Inference Latency:** Average inference latency of **4.2 ms** per telemetry frame on an 8-core virtual machine.

### 6.2 Autonomous Remediation & Telemetry Normalization
Under simulated volumetric flood attacks (SYN Flood, UDP Flood, HTTP GET Flood):
- **Packet Reduction at Edge:** Ingress traffic dropped from 94,000 pkts/s to 110 pkts/s (**99.8% reduction**) within 380 ms of Cloud Armor rule injection.
- **Host CPU Recovery:** Under cryptomining assault (XMRig), host CPU recovered from 94.2% down to 14.5% baseline in **420 ms** following `SIGKILL` dispatch.
- **Safety Veto Enforcement:** 100% of adversarial requests targeting protected entities (`127.0.0.1`, hub IP, or `lsass.exe`) were vetoed by the guardrail engine, preventing self-inflicted denial of service.

---

## 7. Discussion & Governance: The Human-in-the-Loop Principle

A core thesis of AdaptiveCloud is that **full autonomy without human authorization is unsafe for enterprise cloud infrastructure**. While read-only threat detection and dry-run simulations can proceed autonomously, any countermeasure that modifies routing, revokes credentials, or terminates processes must adhere to strict governance principles:

1. **Deterministic Scope Boundaries:** Countermeasures must target a single named host or specific remote CIDR prefix. Subnet-wide blanket shutdowns are rejected by safety guardrails.
2. **1-Click Rollback Guarantee:** Every reversible countermeasure (firewall blocks, WAF rules, bucket permissions) stores a cryptographically signed inversion script allowing instantaneous rollback if identified as a false positive.
3. **Auditable Decision Records:** Every approval, rejection, or expiration is committed immutably to persistent storage (`incidents.db`) with operator identity, rationale comment, and execution timestamp for compliance audits (SOC2, ISO 27001).

---

## 8. Conclusion and Future Directions

AdaptiveCloud demonstrates an operational paradigm shift in cloud security—moving from reactive, alert-heavy advisory dashboards to an evidence-grounded, self-healing framework. By bridging live Google Cloud telemetry with a 238-attack hierarchical taxonomy, dynamic Root Cause Analysis, safety guardrails, and human-in-the-loop permission gates, the platform reduces security MTTR from hours to seconds while preventing destructive remediation mistakes. Future extensions include expanding cross-cloud remediation adapters for AWS and Microsoft Azure, and integrating reinforcement learning to dynamically tune telemetry baselines during organic operational traffic shifts.

---

## References
1. Google Cloud Platform, "Google Cloud Armor Security Policy Overview and DDoS Mitigation," Google Cloud Documentation, 2024.
2. MITRE ATT&CK Framework, "Enterprise Matrix and Cloud Matrix Techniques," MITRE Corporation, 2024.
3. Canadian Institute for Cybersecurity, "CIC-IDS2017 & CSE-CIC-IDS2018 Intrusion Evaluation Datasets," University of New Brunswick, 2018.
4. Open Threat Research Forge (OTRF), "Mordor Datasets: Pre-recorded Security Events," 2023.
5. National Institute of Standards and Technology (NIST), "Special Publication 800-145: The NIST Definition of Cloud Computing," 2011.
6. Cloud Security Alliance (CSA), "Top Threats to Cloud Computing: The Egregious Eleven," CSA Research, 2020.
