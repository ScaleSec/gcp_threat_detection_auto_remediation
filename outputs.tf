
output "topic_name" {
  value = google_pubsub_topic.iam_anomalous_grant_topic.name
  description = "The name of the pub/sub topic where logs are sent to."
}

output "project" {
  value = google_pubsub_topic.iam_anomalous_grant_topic.project
  description = "The Project which hosts the pub/sub topic and subscription resources."
}

output "organization_sink_writer" {
  value       = google_logging_organization_sink.iam_anomalous_grant_log_sink.writer_identity
  description = "The Service Account associated with the organization sink."
}

output "function_name" {
  value       = google_cloudfunctions_function.iam_anomalous_grant_function.name
  description = "The Cloud Function that performs the IAM administration."
}