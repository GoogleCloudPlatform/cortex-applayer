# Copyright 2024 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

variable "project_id" {
  type        = string
  description = "The GCP project ID"
  nullable    = false
}

variable "region" {
  type        = string
  description = "The region for Cloud Run and Cloud Scheduler"
  nullable    = false
}

variable "cloud_run_job_name" {
  type        = string
  description = "Name of Cloud Run job resource to create"
  default     = "sfdc2bq"
  nullable    = false
}

variable "scheduler_name" {
  type        = string
  description = "Name of Cloud Scheduler resource to create"
  default     = null
}

variable "service_account" {
  type        = string
  description = "The name of the service account for sfdc2bq, it's the username part of the service account's email (username@PROJECT_ID.iam.gserviceaccount.com)"
  default     = "sfdc2bq-sa"
  nullable    = false
}

variable "job_schedule_cron" {
  type        = string
  description = "Cron schedule string for the job"
  default     = "0 * * * *" # Every hour by default
  nullable    = false
}

locals {
  container_tag  = "gcr.io/${var.project_id}/${var.cloud_run_job_name}:latest"
  scheduler_name = var.scheduler_name != null ? var.scheduler_name : "${var.cloud_run_job_name}-cron"
}

variable "bq_project_id" {
  type        = string
  description = "The project ID for the BigQuery dataset"
  nullable    = false
}

variable "bq_dataset" {
  type        = string
  description = "The ID of the BigQuery dataset"
  nullable    = false
}

variable "use_existing_dataset" {
  type        = bool
  description = "Whether to use an existing BigQuery dataset instead of creating one"
  default     = false
}

variable "store_sfdc_metadata" {
  type        = bool
  description = "Whether to store SFDC object metadata in _sfdc_metadata table"
  default     = true
}

variable "bq_location" {
  type        = string
  description = "The location of the BigQuery dataset"
  nullable    = false
}

variable "sfdc_objects" {
  type        = string
  description = "Comma-separated list of Salesforce objects to replicate"
  default     = "Account,Case,Contact,Event,Lead,Opportunity,Task,User"
  nullable    = false
}

variable "parallel_tasks" {
  type        = number
  description = "Number of parallel jobs. Can be up to the numbber of replicated Salesforce objects"
  default     = 3
}

variable "sfdc_auth_secret_name" {
  type        = string
  description = "The ID of the Secret Manager secret for Salesforce authentication"
  default     = "sfdc-auth"
  nullable    = false
}

variable "sfdc_auth_secret_data" {
  type        = string
  description = "The actual Salesforce authentication secret data. Keep it empty if the secret already exists."
  sensitive   = true
  nullable    = false
}
