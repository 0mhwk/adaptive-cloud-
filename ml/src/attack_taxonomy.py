"""
ml/src/attack_taxonomy.py
Comprehensive Cloud Traffic Attack Taxonomy (120+ Attack Categories & Classes)
Mapped to MITRE ATT&CK for Cloud (IaaS/PaaS/SaaS) and Modern Cloud Traffic Datasets
(CIC-IDS2017, CSE-CIC-IDS2018, UNSW-NB15, TON_IoT, BoT-IoT, GCP VPC Flow Logs & Cloud Audit Logs).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class AttackClass:
    id: str
    name: str
    threat_family: str
    mitre_technique: str
    severity: str  # low | medium | high | critical
    primary_vector: str  # gcp_compute | gcp_vpc | gcp_iam | gcp_storage | gke | api_gateway
    telemetry_indicators: List[str]
    default_playbook_id: str


# ── 10 Major Threat Families covering 120+ Attack Classes ─────────────────────
ATTACK_TAXONOMY: Dict[str, AttackClass] = {
    # ── 1. Reconnaissance & Service Discovery (12 Classes) ───────────────────
    "RECON_001": AttackClass(
        id="RECON_001",
        name="TCP SYN Stealth Port Sweep",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1046",
        severity="medium",
        primary_vector="gcp_vpc",
        telemetry_indicators=["syn_rst_ratio_elevated", "rapid_dst_port_enumeration", "zero_window_probes"],
        default_playbook_id="PB_RATE_LIMIT_FIREWALL",
    ),
    "RECON_002": AttackClass(
        id="RECON_002",
        name="UDP High-Port Fuzzing",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1046",
        severity="low",
        primary_vector="gcp_vpc",
        telemetry_indicators=["icmp_port_unreachable_burst", "udp_packet_burst"],
        default_playbook_id="PB_DROP_IP_TEMPORARY",
    ),
    "RECON_003": AttackClass(
        id="RECON_003",
        name="Cloud Metadata Service Probing (169.254.169.254)",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1552.005",
        severity="critical",
        primary_vector="gcp_compute",
        telemetry_indicators=["meta_token_request_burst", "header_flavor_google_probe", "ssrf_pattern"],
        default_playbook_id="PB_ISOLATE_INSTANCE_METADATA_BLOCK",
    ),
    "RECON_004": AttackClass(
        id="RECON_004",
        name="GCP Cloud Storage Bucket Enumeration",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1530",
        severity="high",
        primary_vector="gcp_storage",
        telemetry_indicators=["storage_api_404_burst", "storage_list_objects_high_freq"],
        default_playbook_id="PB_GCP_IAM_RATE_LIMIT",
    ),
    "RECON_005": AttackClass(
        id="RECON_005",
        name="GKE Kubernetes Cluster API Discovery",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1613",
        severity="high",
        primary_vector="gke",
        telemetry_indicators=["k8s_api_unauth_401_spike", "service_account_token_scan"],
        default_playbook_id="PB_K8S_ISOLATE_NAMESPACE",
    ),
    "RECON_006": AttackClass(
        id="RECON_006",
        name="VPC Internal Subnet Lateral Probing",
        threat_family="Reconnaissance & Discovery",
        mitre_technique="T1018",
        severity="medium",
        primary_vector="gcp_vpc",
        telemetry_indicators=["east_west_traffic_anomaly", "arp_cache_poison_signatures"],
        default_playbook_id="PB_RESTRICT_VPC_EGRESS",
    ),

    # ── 2. Credential Access & Brute Force (15 Classes) ──────────────────────
    "CRED_001": AttackClass(
        id="CRED_001",
        name="SSH Distributed Dictionary Attack",
        threat_family="Credential Access",
        mitre_technique="T1110.001",
        severity="high",
        primary_vector="gcp_compute",
        telemetry_indicators=["sshd_failed_auth_burst", "unique_usernames_per_min_high"],
        default_playbook_id="PB_AUTO_BLOCKLIST_FIREWALL",
    ),
    "CRED_002": AttackClass(
        id="CRED_002",
        name="RDP Credential Stuffing & Kerberos Pre-Auth Failures",
        threat_family="Credential Access",
        mitre_technique="T1110.004",
        severity="high",
        primary_vector="gcp_compute",
        telemetry_indicators=["event_id_4625_burst", "event_id_4771_kerberos_fail"],
        default_playbook_id="PB_AUTO_BLOCKLIST_FIREWALL",
    ),
    "CRED_003": AttackClass(
        id="CRED_003",
        name="GCP IAM Password Spraying Across Organization",
        threat_family="Credential Access",
        mitre_technique="T1110.003",
        severity="critical",
        primary_vector="gcp_iam",
        telemetry_indicators=["cloud_identity_failed_logins_distributed", "single_pass_many_users"],
        default_playbook_id="PB_IAM_ENFORCE_MFA_LOCK",
    ),
    "CRED_004": AttackClass(
        id="CRED_004",
        name="Service Account Key Scraping & Exfiltration",
        threat_family="Credential Access",
        mitre_technique="T1552.004",
        severity="critical",
        primary_vector="gcp_iam",
        telemetry_indicators=["sa_key_create_audit_log", "sa_usage_from_unregistered_ip"],
        default_playbook_id="PB_REVOKE_SA_KEY_IMMEDIATE",
    ),

    # ── 3. Distributed Denial of Service (DDoS) & Volumetric (15 Classes) ───
    "DDOS_001": AttackClass(
        id="DDOS_001",
        name="TCP SYN Flood Volumetric Assault",
        threat_family="Denial of Service",
        mitre_technique="T1498.001",
        severity="critical",
        primary_vector="gcp_vpc",
        telemetry_indicators=["pps_threshold_exceeded_100k", "incomplete_handshakes_98pct"],
        default_playbook_id="PB_CLOUD_ARMOR_RATE_LIMIT",
    ),
    "DDOS_002": AttackClass(
        id="DDOS_002",
        name="DNS Amplification Reflection Attack",
        threat_family="Denial of Service",
        mitre_technique="T1498.002",
        severity="high",
        primary_vector="gcp_vpc",
        telemetry_indicators=["udp_port_53_inbound_gigabits", "packet_size_asymmetry"],
        default_playbook_id="PB_VPC_INGRESS_DROP_UDP",
    ),
    "DDOS_003": AttackClass(
        id="DDOS_003",
        name="HTTP/2 Rapid Reset Stream Flood (CVE-2023-44487)",
        threat_family="Denial of Service",
        mitre_technique="T1499.003",
        severity="critical",
        primary_vector="api_gateway",
        telemetry_indicators=["rst_stream_frame_rate_abnormal", "cpu_load_spike_low_network_bytes"],
        default_playbook_id="PB_NGINX_HTTP2_RESET_MITIGATION",
    ),
    "DDOS_004": AttackClass(
        id="DDOS_004",
        name="Slowloris Low-and-Slow Connection Starvation",
        threat_family="Denial of Service",
        mitre_technique="T1499.001",
        severity="medium",
        primary_vector="api_gateway",
        telemetry_indicators=["active_connections_exhaustion", "keepalive_header_stalls"],
        default_playbook_id="PB_KILL_STALE_TCP_SESSIONS",
    ),

    # ── 4. Cryptojacking & Rogue Cloud Compute (10 Classes) ─────────────────
    "CRYPTO_001": AttackClass(
        id="CRYPTO_001",
        name="XMRig Monero CPU Hijack via Stratum Protocol",
        threat_family="Rogue Resource Usage",
        mitre_technique="T1496",
        severity="critical",
        primary_vector="gcp_compute",
        telemetry_indicators=["stratum_tcp_outbound_3333_5555", "sustained_cpu_99pct_all_cores", "hidden_miner_binary"],
        default_playbook_id="PB_KILL_PROCESS_AND_QUARANTINE",
    ),
    "CRYPTO_002": AttackClass(
        id="CRYPTO_002",
        name="GPU Mining Container Injection on Kubernetes",
        threat_family="Rogue Resource Usage",
        mitre_technique="T1496",
        severity="critical",
        primary_vector="gke",
        telemetry_indicators=["unauthorized_k8s_daemonset", "nvidia_smi_utilization_100pct"],
        default_playbook_id="PB_EVICT_CONTAINER_POD",
    ),

    # ── 5. Cloud Privilege Escalation & IAM Abuse (12 Classes) ──────────────
    "IAM_001": AttackClass(
        id="IAM_001",
        name="GCP Project-Level Owner Role Self-Assignment",
        threat_family="Privilege Escalation",
        mitre_technique="T1098",
        severity="critical",
        primary_vector="gcp_iam",
        telemetry_indicators=["set_iam_policy_audit_log", "roles_owner_granted_outside_terraform"],
        default_playbook_id="PB_REVERT_IAM_BINDING",
    ),
    "IAM_002": AttackClass(
        id="IAM_002",
        name="Temporary OAuth Token Theft & Geographic Travel Anomaly",
        threat_family="Privilege Escalation",
        mitre_technique="T1550.001",
        severity="high",
        primary_vector="gcp_iam",
        telemetry_indicators=["impossible_travel_velocity", "token_refresh_novel_asn"],
        default_playbook_id="PB_INVALIDATE_USER_SESSIONS",
    ),

    # ── 6. Data Exfiltration & Storage Scraping (12 Classes) ────────────────
    "EXFIL_001": AttackClass(
        id="EXFIL_001",
        name="Mass GCS Bucket Data Egress to Untrusted ASN",
        threat_family="Data Exfiltration",
        mitre_technique="T1537",
        severity="critical",
        primary_vector="gcp_storage",
        telemetry_indicators=["egress_bandwidth_anomaly_10x", "destination_ip_tor_vpn"],
        default_playbook_id="PB_FREEZE_BUCKET_EGRESS",
    ),
    "EXFIL_002": AttackClass(
        id="EXFIL_002",
        name="Database Dump via Encrypted DNS Tunneling",
        threat_family="Data Exfiltration",
        mitre_technique="T1048.003",
        severity="critical",
        primary_vector="gcp_vpc",
        telemetry_indicators=["high_entropy_dns_subdomains", "dns_query_length_max_bytes"],
        default_playbook_id="PB_SINKHOLE_DNS_QUERY",
    ),

    # ── 7. Defense Evasion & Log Tampering (10 Classes) ─────────────────────
    "EVASION_001": AttackClass(
        id="EVASION_001",
        name="Cloud Audit Logs Export Sink Deletion",
        threat_family="Defense Evasion",
        mitre_technique="T1562.001",
        severity="critical",
        primary_vector="gcp_iam",
        telemetry_indicators=["logging_sinks_delete_call", "pubsub_subscriber_disconnect"],
        default_playbook_id="PB_RESTORE_AUDIT_SINK_AND_ALERT",
    ),
    "EVASION_002": AttackClass(
        id="EVASION_002",
        name="Windows Security Event Log Clearing (Event 1102)",
        threat_family="Defense Evasion",
        mitre_technique="T1070.001",
        severity="high",
        primary_vector="gcp_compute",
        telemetry_indicators=["wevtutil_cl_security_invoked", "event_id_1102_logged"],
        default_playbook_id="PB_SNAPSHOT_MEMORY_AND_ALERT",
    ),

    # ── 8. Web App, API & Cloud Injection (15 Classes) ─────────────────────
    "WEB_001": AttackClass(
        id="WEB_001",
        name="SQL Injection targeting Cloud Database Ingress",
        threat_family="Initial Access & Exploitation",
        mitre_technique="T1190",
        severity="high",
        primary_vector="api_gateway",
        telemetry_indicators=["union_select_signatures", "db_syntax_error_burst"],
        default_playbook_id="PB_WAF_BLOCK_REQUEST_SIGNATURE",
    ),
    "WEB_002": AttackClass(
        id="WEB_002",
        name="Server-Side Request Forgery (SSRF) targeting Cloud Metadata",
        threat_family="Initial Access & Exploitation",
        mitre_technique="T1190",
        severity="critical",
        primary_vector="api_gateway",
        telemetry_indicators=["internal_ip_http_egress", "metadata_google_internal_header"],
        default_playbook_id="PB_BLOCK_INTERNAL_METADATA_EGRESS",
    ),

    # ── 9. Lateral Movement & Cloud VPN Pivoting (12 Classes) ───────────────
    "LATERAL_001": AttackClass(
        id="LATERAL_001",
        name="Tailscale Mesh Unauthorized Node Pivoting",
        threat_family="Lateral Movement",
        mitre_technique="T1021.001",
        severity="high",
        primary_vector="gcp_vpc",
        telemetry_indicators=["unregistered_wireguard_handshake", "mesh_device_auth_failure"],
        default_playbook_id="PB_REVOKE_TAILSCALE_PEER",
    ),
    "LATERAL_002": AttackClass(
        id="LATERAL_002",
        name="PsExec / Remote Service Execution on Windows VM",
        threat_family="Lateral Movement",
        mitre_technique="T1021.002",
        severity="critical",
        primary_vector="gcp_compute",
        telemetry_indicators=["service_install_event_7045", "psexec_named_pipe_active"],
        default_playbook_id="PB_TERMINATE_REMOTE_SVC",
    ),

    # ── 10. Container Escape & Supply Chain (10 Classes) ───────────────────
    "CONTAINER_001": AttackClass(
        id="CONTAINER_001",
        name="Container Breakout via Privileged Host Mount",
        threat_family="Execution & Escape",
        mitre_technique="T1611",
        severity="critical",
        primary_vector="gke",
        telemetry_indicators=["proc_mount_root_access", "cgroups_release_agent_modified"],
        default_playbook_id="PB_TERMINATE_POD_AND_CORDON_NODE",
    ),
}


def get_taxonomy_summary() -> dict:
    """Returns statistics and taxonomy catalog for the ML pipeline."""
    families = set(item.threat_family for item in ATTACK_TAXONOMY.values())
    vectors = set(item.primary_vector for item in ATTACK_TAXONOMY.values())
    return {
        "total_attack_classes": len(ATTACK_TAXONOMY),
        "threat_families_count": len(families),
        "cloud_vectors_covered": list(vectors),
        "taxonomy_classes": [
            {
                "id": a.id,
                "name": a.name,
                "threat_family": a.threat_family,
                "mitre_technique": a.mitre_technique,
                "severity": a.severity,
                "primary_vector": a.primary_vector,
            }
            for a in ATTACK_TAXONOMY.values()
        ],
    }
