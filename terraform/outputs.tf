output "cloud_run_url" {
  description = "URL del servizio Cloud Run"
  value       = google_cloud_run_v2_service.api.uri
}

output "artifact_registry_url" {
  description = "URL Artifact Registry"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/runner-platform"
}

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}
