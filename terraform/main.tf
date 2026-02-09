terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Backend per salvare lo state (opzionale, ma raccomandato)
  # Commentato per il primo deploy, poi abilita
  # backend "gcs" {
  #   bucket = "runner-platform-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Abilita API necessarie
resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com"
  ])
  
  service            = each.key
  disable_on_destroy = false
}

# Artifact Registry per container images
resource "google_artifact_registry_repository" "runner_platform" {
  location      = var.region
  repository_id = "runner-platform"
  description   = "Docker images for Runner Platform"
  format        = "DOCKER"
  
  depends_on = [google_project_service.required_apis]
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "api" {
  name     = "runner-platform-api"
  location = var.region
  
  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/runner-platform/api:latest"
      
      # Environment variables
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      
      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      
      # Resource limits (ottimizzato per costi bassi)
      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true  # Scale to zero quando idle
      }
      
      # Health check
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        timeout_seconds       = 3
        period_seconds        = 10
        failure_threshold     = 3
      }
      
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds    = 30
        timeout_seconds   = 3
        failure_threshold = 3
      }
    }
    
    # Scaling configuration (aggressivo per ridurre costi)
    scaling {
      min_instance_count = 0  # Scale to zero
      max_instance_count = 5
    }
    
    # Timeout
    timeout = "300s"
  }
  
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
  
  depends_on = [
    google_project_service.required_apis,
    google_artifact_registry_repository.runner_platform
  ]
}

# IAM policy per accesso pubblico (non autenticato)
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.api.location
  service  = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Log bucket (retention breve per ridurre costi)
resource "google_logging_project_bucket_config" "basic" {
  project        = var.project_id
  location       = "global"
  retention_days = 7
  bucket_id      = "_Default"
  
  depends_on = [google_project_service.required_apis]
}

# Monitoring alert per costi elevati (opzionale)
resource "google_monitoring_alert_policy" "high_cost_alert" {
  display_name = "High Cloud Run Costs"
  combiner     = "OR"
  
  conditions {
    display_name = "Cloud Run request count > 10000/hour"
    
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"run.googleapis.com/request_count\""
      duration        = "3600s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10000
      
      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = []  # Aggiungi email se vuoi notifiche
  
  alert_strategy {
    auto_close = "604800s"  # 7 giorni
  }
  
  depends_on = [google_project_service.required_apis]
}
