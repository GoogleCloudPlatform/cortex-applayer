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

project_id = "" # Project where to deploy Cloud Run job and Cloud Scheduler job.

region             = "us-central1"  # Compute region for Cloud Run and Cloud Scheduler.
service_account    = "sfdc2bq-sa"   # Service account name to use with Cloud Run and Cloud Scheduler.
cloud_run_job_name = "sfdc2bq"      # Cloud Run job name.
scheduler_name     = "sfdc2bq-cron" # Cloud Scheduler name.
job_schedule_cron  = "0 * * * *"    # Every hour

bq_project_id        = ""    # Project where BigQuery data will reside.
bq_dataset           = ""    # Dataset name.
bq_location          = "US"  # BigQuery location. Co-locate it with Cloud Run region when posible (e.g. US with us-central1).
use_existing_dataset = false # Set to true if BigQuery dataset already exists.

sfdc_objects   = "Account,Case,Contact,Event,Lead,Opportunity,Task,User"
parallel_tasks = 8 # Adjust to the number of object in the list above

# Secret Manager secret name to store SFDC authentication data. Must be in the same project as specified in project_id.
# If sfdc_auth_secret_data below is empty, it means the secret already exists.
sfdc_auth_secret_name = "sfdc-auth"

# * ConsumerKey and ConsumerSecret are respective attributes of a Connected App with OAuth 2.0 Client Credentials Flow
#   Create one as described in https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm&type=5
#   Get ConsumerKey and ConsumerSecret in the App Manager (App Manager -> [your app] -> View -> Manage Consumer Details)
#
# * domain is MyDomainName part in https://MyDomainName.my.salesforce.com as described in https://help.salesforce.com/s/articleView?id=sf.faq_domain_name_what.htm&type=5
#
# Keep sfdc_auth_secret_data empty if the secret already exists.
sfdc_auth_secret_data = <<_EOT
    {
        "ConsumerKey": "",
        "ConsumerSecret": "",
        "Domain": ""
    }
_EOT
