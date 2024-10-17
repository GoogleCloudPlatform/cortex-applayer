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

resource "google_project_service" "bq_project_services" {
  project = var.bq_project_id
  for_each = toset([
    "bigquery.googleapis.com",
    "iam.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}
resource "google_project_service" "project_services" {
  project = var.project_id
  for_each = toset([
    "iam.googleapis.com",
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com"
  ])
  service            = each.value
  disable_on_destroy = false
}

resource "terraform_data" "build_image" {
  provisioner "local-exec" {
    command = "gcloud builds submit --tag ${local.container_tag} --project ${var.project_id} ../.."
  }
  depends_on = [google_project_service.project_services]
}

data "google_project" "project" {
  project_id = var.project_id
}

resource "google_bigquery_dataset" "bq_dataset" {
  project                    = var.bq_project_id
  location                   = var.bq_location
  dataset_id                 = var.bq_dataset
  count                      = var.use_existing_dataset ? 0 : 1
  delete_contents_on_destroy = false
  lifecycle {
    prevent_destroy = true
  }
  depends_on = [google_project_service.bq_project_services]
}

resource "google_service_account" "default" {
  account_id                   = var.service_account
  display_name                 = "Service Account for ${var.cloud_run_job_name}"
  project                      = var.project_id
  create_ignore_already_exists = true
  depends_on                   = [google_project_service.project_services]
}

resource "google_bigquery_dataset_iam_member" "dataset_access" {
  project    = var.bq_project_id
  dataset_id = var.bq_dataset
  role       = "roles/bigquery.dataEditor" # Grant appropriate permissions
  member     = "serviceAccount:${google_service_account.default.email}"
  depends_on = [google_bigquery_dataset.bq_dataset, google_service_account.default]
}

resource "google_project_iam_member" "bq_job_user" {
  project    = var.bq_project_id
  role       = "roles/bigquery.jobUser"
  member     = "serviceAccount:${google_service_account.default.email}"
  depends_on = [google_project_service.bq_project_services, google_service_account.default]
}

resource "google_secret_manager_secret" "sfdc_auth" {
  project = var.project_id

  replication {
    auto {
    }
  }

  secret_id  = var.sfdc_auth_secret_name
  count      = length(trimspace(var.sfdc_auth_secret_data)) > 0 ? 1 : 0 # Empty secret data means that secret already exists.
  depends_on = [google_project_service.project_services]
}

data "google_secret_manager_secret" "sfdc_auth" {
  project    = var.project_id
  secret_id  = var.sfdc_auth_secret_name
  depends_on = [google_secret_manager_secret.sfdc_auth]
}

resource "google_secret_manager_secret_version" "sfdc_auth" {
  secret_data = var.sfdc_auth_secret_data
  secret      = data.google_secret_manager_secret.sfdc_auth.id
  enabled     = true
  count       = length(trimspace(var.sfdc_auth_secret_data)) > 0 ? 1 : 0
}

resource "google_secret_manager_secret_iam_member" "secret_accessor" {
  project   = var.project_id
  secret_id = data.google_secret_manager_secret.sfdc_auth.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.default.email}"
}


resource "google_cloud_run_v2_job" "default" {
  name     = var.cloud_run_job_name
  project  = var.project_id
  location = var.region
  template {
    template {
      containers {
        image = local.container_tag

        env {
          name  = "BQ_PROJECT"
          value = var.bq_project_id
        }
        env {
          name  = "BQ_DATASET"
          value = var.bq_dataset
        }
        env {
          name  = "BQ_LOCATION"
          value = var.bq_location
        }
        env {
          name  = "SFDC_AUTH_SECRET"
          value = "${data.google_secret_manager_secret.sfdc_auth.id}/versions/latest"
        }
        env {
          name  = "SFDC_OBJECTS"
          value = var.sfdc_objects
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "4Gi"
          }
        }
      }
      timeout         = "43200s" # 12 hours
      service_account = google_service_account.default.email
    }
    task_count = var.parallel_tasks
  }
  depends_on = [terraform_data.build_image,
    google_bigquery_dataset_iam_member.dataset_access,
    google_secret_manager_secret_iam_member.secret_accessor,
    google_project_service.project_services,
    google_project_service.bq_project_services
  ]
}

resource "google_cloud_run_v2_job_iam_member" "cloud_run_invoker" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_job.default.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.default.email}"
}


resource "google_cloud_scheduler_job" "default" {
  name             = local.scheduler_name
  region           = var.region
  project          = var.project_id
  schedule         = var.job_schedule_cron
  time_zone        = "UTC" # Set your desired timezone
  attempt_deadline = "600s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.cloud_run_job_name}:run"
    oauth_token {
      service_account_email = google_service_account.default.email
    }
  }
  depends_on = [google_cloud_run_v2_job_iam_member.cloud_run_invoker]
}
