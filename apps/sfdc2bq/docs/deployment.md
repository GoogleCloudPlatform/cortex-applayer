# Salesforce.com to BigQuery data transfer

## SFDC2BQ Deployment

This tutorial will guide you through **SFDC2BQ** configuration and deployment.

Click the **Start** button to move to the next step.

## Specify configuration variables

* <walkthrough-editor-open-file filePath="src/deployment/terraform/terraform.tfvars">Open `src/deployment/terraform/terraform.tfvars` file</walkthrough-editor-open-file>.
* Specify values for all variables.

> **Configuring BigQuery dataset**
>
> `use_existing_dataset` controls whether the deployment should use an existing dataset with the name specified in `bq_dataset`.

> **Configuring `sfdc_auth_secret_data`**
>
> `ConsumerKey` and `ConsumerSecret` are respective attributes of a [Connected App with OAuth 2.0 Client Credentials Flow](https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm&type=5). You need to create one for SFDC2BQ.
Make sure the user in `Run As` option has permissions to read all objects you would like to replicate.
>
> Get `ConsumerKey` and `ConsumerSecret` in the App Manager (`App Manager -> [your app] -> View -> Manage Consumer Details`)
>
> You can also use an existing secret. In that case, keep `sfdc_auth_secret_data` value empty.

## Execute the deployment

Run the deployment script:

```bash
src/deployment/deploy_terraform.sh
```

## Conclusion

Thank you for using SFDC2BQ!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>
