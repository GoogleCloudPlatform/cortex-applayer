# SFDC2BQ: Salesforce.com to BigQuery connector

[Salesforce.com (SFDC)](https://www.salesforce.com/) to [Google Cloud BigQuery](https://cloud.google.com/bigquery) data replication connector.

A fast and efficient data transfer service running in [Google Cloud Run](https://cloud.google.com/run) with [Cloud Scheduler](https://cloud.google.com/scheduler/docs).

## Disclaimer

> This is not an official Google product

## Deployment

`src/deployment` contains terraform scripts for deploying SFDC2BQ.

* Configure the deployment with variables in `src/deployment/terraform/terraform.tfvars` file.
* Run `src/deployment/deploy_terraform.sh` to execute the deployment.

Use `Open in Google Cloud Shell` button below to deploy SFDC2BQ from Google Cloud Shell.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?show=ide%2Cterminal&cloudshell_git_repo=https%3A%2F%2Fgithub.com%2FGoogleCloudPlatform%2Fcortex-applayer&cloudshell_open_in_editor=src%2Fdeployment%2Fterraform%2Fterraform.tfvars&cloudshell_tutorial=docs%2Fdeployment.md&cloudshell_workspace=apps%2Fsfdc2bq)
