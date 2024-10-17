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

output "cloud_run_service_id" {
  value       = google_cloud_run_v2_job.default.id
  description = "Id of the deployed Cloud Run job"
}

output "bigquery_dataset" {
  value       = "${var.bq_project_id}.${var.bq_dataset}"
  description = "Created BigQuery dataset name with the project"
}

output "service_account_email" {
  value       = google_service_account.default.email
  description = "The email address of the created service account"
}

output "secret_manager_secret" {
  value       = data.google_secret_manager_secret.sfdc_auth.name
  description = "The name of the created Secret Manager secret"

}

output "cloud_scheduler_job" {
  value       = google_cloud_scheduler_job.default.id
  description = "The id of the created Cloud Scheduler job"
}
