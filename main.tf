data "google_client_config" "current" {
}

provider "google" {
  project = var.project
  region  = var.region
}

provider "google-beta" {
  project = var.project
  region  = var.region
}

locals {
  function_name = "${lower(var.name)}-iam-anomalous-grant"
}

provider "archive" {
  version = "1.3"
}

resource "google_logging_organization_sink" "iam_anomalous_grant_log_sink" {
  name             = "${var.org_id}-iam-anomalous-grant-log-sink"
  org_id           = var.org_id
  destination      = "pubsub.googleapis.com/projects/${var.project}/topics/${google_pubsub_topic.iam_anomalous_grant_topic.name}"
  filter           = var.org_sink_filter
  include_children = true
}

resource "random_id" "sa-id" {
  byte_length = 4
}

resource "google_pubsub_topic" "iam_anomalous_grant_topic" {
  name    = "${lower(var.name)}-iam-anomalous-grant-topic"
  project = var.project
}

resource "google_pubsub_topic_iam_member" "publisher" {
  project = var.project
  topic   = google_pubsub_topic.iam_anomalous_grant_topic.name
  role    = "roles/pubsub.publisher"
  member  = google_logging_organization_sink.iam_anomalous_grant_log_sink.writer_identity
}

data "archive_file" "source" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/iam_anomalous_grant.zip"
}

resource "google_storage_bucket" "bucket" {
  provider = google
  project  = var.project
  name     = "${lower(var.name)}-iam-anomalous-grant-${var.project}"
}

resource "google_storage_bucket_object" "archive" {
  provider = google
  name     = "src-${lower(replace(base64encode(data.archive_file.source.output_md5), "=", ""))}.zip"
  bucket   = google_storage_bucket.bucket.name
  source   = data.archive_file.source.output_path
}

resource "google_service_account" "iam_anomalous_grant_sa" {
  account_id   = "${lower(var.name)}-iam-anomalous-grant"
  display_name = "${var.name} IAM anomalous grant"
}

resource "google_organization_iam_custom_role" "iam_anomalous_grant_custom_role" {
  role_id     = "iam_anomalous_grant_cfn"
  org_id      = var.org_id
  title       = "Iam Anomalous Grant Cloud Function Role"
  description = "Minimally Privlidged Role to manage IAM policies."
  permissions = ["resourcemanager.organizations.getIamPolicy", "resourcemanager.projects.getIamPolicy", "resourcemanager.projects.setIamPolicy", "resourcemanager.organizations.setIamPolicy", "logging.logEntries.create"]
}

resource "google_organization_iam_member" "iam_anomalous_grant_member" {
  org_id = var.org_id
  role   = "organizations/${var.org_id}/roles/${google_organization_iam_custom_role.iam_anomalous_grant_custom_role.role_id}"
  member = "serviceAccount:${google_service_account.iam_anomalous_grant_sa.email}"
}

resource "google_cloudfunctions_function" "iam_anomalous_grant_function" {
  provider              = google-beta
  name                  = local.function_name
  description           = "Google Cloud Function to remediate Event Threat Detector IAM anomalous grant findings."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  timeout               = 60
  entry_point           = "process_log_entry"
  service_account_email = google_service_account.iam_anomalous_grant_sa.email
  runtime               = "python37"

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.iam_anomalous_grant_topic.name
  }
}
