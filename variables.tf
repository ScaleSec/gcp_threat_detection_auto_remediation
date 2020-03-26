variable "org_id" {
  description = "The Organization to associate the project"
}

variable "project" {
  description = "The Project to deploy resources to"
}

variable "region" {
  description = "The Region which to deploy resources into"
  default     = "us-east1"
}

variable "name" {
  description = "The Prefix to apply to resource names."
  default     = "etd"
}

variable "org_sink_filter" {
  description = "The Log Filter to apply to the Org Level export."
  default     = "resource.type:threat_detector resource.labels.detector_name=iam_anomalous_grant"
}