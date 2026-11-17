# deploy/gcp/terraform/main.tf
# Terraform configuration for provisioning native GCP resources for AdaptiveCloud

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
  default     = "adaptive-learning-ml"
}

variable "region" {
  description = "Default Google Cloud Region"
  type        = string
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── 1. VPC Network & Subnet with Flow Logs Enabled ───────────────────────────
resource "google_compute_network" "adaptive_vpc" {
  name                    = "adaptivecloud-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "adaptive_subnet" {
  name          = "adaptivecloud-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.adaptive_vpc.id

  # Native VPC Flow Logs for network threat detection
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = 0.5
    metadata             = "INCLUDE_ALL_METADATA"
  }
}

# ── 2. Google Cloud Armor Security Policy (DDoS & SYN Rate-Limiting) ──────────
resource "google_compute_security_policy" "cloud_armor_waf" {
  name        = "cloud-armor-adaptive-waf"
  description = "AdaptiveCloud edge DDoS mitigation and automated rate-limiting policy"

  # Default allow rule
  rule {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["*"]
      }
    }
    description = "Default allow"
  }

  # Rate-limiting rule against volumetric SYN floods
  rule {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "SRC_IPS_V1"
      config {
        src_ip_ranges = ["198.51.100.0/24"]
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action  = "deny(429)"
      enforce_on_key = "IP"
      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }
      ban_duration_sec = 3600
    }
    description = "Automated edge rate-limiting deployed by AdaptiveCloud Self-Healing engine"
  }
}

# ── 3. Central Gateway Compute Instance (GCP-VM-EU-02) ────────────────────────
resource "google_compute_instance" "gateway_vm" {
  name         = "gcp-vm-eu-02"
  machine_type = "e2-medium"
  zone         = "${var.region}-a"

  boot_disk {
    initialize_params {
      image = "windows-cloud/windows-server-2022-dc-v20240111"
      size  = 50
    }
  }

  network_interface {
    network    = google_compute_network.adaptive_vpc.id
    subnetwork = google_compute_subnetwork.adaptive_subnet.id
    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    enable-oslogin = "TRUE"
  }

  tags = ["adaptivecloud-gateway", "secops-monitored"]
}

# ── 4. Cloud Pub/Sub Telemetry Topic ──────────────────────────────────────────
resource "google_pubsub_topic" "telemetry_topic" {
  name = "adaptivecloud-telemetry-stream"
}

# ── 5. Cloud Storage Secure Bucket (Uniform Bucket-Level Access) ──────────────
resource "google_storage_bucket" "secure_backup_bucket" {
  name                        = "${var.project_id}-adaptive-backups"
  location                    = var.region
  uniform_bucket_level_access = true
  versioning {
    enabled = true
  }
}

# ── 6. IAM Service Account for Least-Privilege Agent Telemetry ────────────────
resource "google_service_account" "agent_sa" {
  account_id   = "adaptivecloud-collector"
  display_name = "AdaptiveCloud Agent Telemetry Collector"
}

resource "google_project_iam_member" "monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}

resource "google_project_iam_member" "logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.agent_sa.email}"
}
