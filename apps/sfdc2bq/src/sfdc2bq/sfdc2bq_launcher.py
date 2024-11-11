# Copyright 2022 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" This module provides SFDC -> BigQuery extraction bootstrapper  """

import json
import typing
from urllib.parse import unquote, urlparse, parse_qs

from google.api_core.client_info import ClientInfo
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from google.cloud import secretmanager

from simple_salesforce import Salesforce  # type: ignore

# pylint:disable=wrong-import-position
from sfdc2bq import sfdc2bq_replicate  # type: ignore

SFDC2BQ_USER_AGENT = f"sfdc2bq/1.0 (GPN:SFDC2BQ;)"


def replicate_sfdc_object_to_bq(
    sfdc_auth_parameters: typing.Union[str, typing.Dict[str, str]],
    api_name: str,
    bq_project_id: str,
    bq_dataset_name: str,
    bq_output_table_name: typing.Optional[str] = None,
    bq_location: str = "US",
    store_metadata: bool = False
) -> None:
    """Replicates a single SFDC object to BigQuery

    Args:
        sfdc_auth_parameters (typing.Union[str, typing.Dict[str, str]]):
            May be string or a string dictionary.
            - If a string, it should be a Secret Manager secret version name
              (projects/PROJECT_NUMBER/secrets/SECRET_NAME/versions/latest)
              The secret value may be an Airflow connection string for Salesforce (salesforce://)
              or a json text. Json text will be converted to a dictionary
              (see dictionary details below).
            - If a dictionary, it must contain a valid combination of these parameters,
                as described here https://github.com/simple-salesforce/simple-salesforce/blob/1d28fa18438d3840140900d4c00799798bad57b8/simple_salesforce/api.py#L65
                    * domain -- The domain to using for connecting to Salesforce. Use
                                    common domains, such as 'login' or 'test', or
                                    Salesforce My domain. If not used, will default to
                                    'login'.

                    -- Password Authentication:
                        * username -- the Salesforce username to use for authentication
                        * password -- the password for the username
                        * security_token -- the security token for the username

                    -- OAuth 2.0 Connected App Token Authentication:
                        * consumer_key -- the consumer key generated for the user
                        * consumer_secret -- the consumer secret generated for the user

                    -- OAuth 2.0 JWT Bearer Token Authentication:
                        * consumer_key -- the consumer key generated for the user

                    Then either
                        * privatekey_file -- the path to the private key file used
                                            for signing the JWT token
                        OR
                        * privatekey -- the private key to use
                                        for signing the JWT token

                    -- Direct Session and Instance Access:
                        * session_id -- Access token for this session

                    Then either
                        * instance -- Domain of your Salesforce instance, i.e.
                        `na1.salesforce.com`
                        OR
                        * instance_url -- Full URL of your instance i.e.
                        `https://na1.salesforce.com

        api_name (str): API/Object name (account, opportunity, user, etc.)
        bq_project_id (str): Target GCP project name.
        bq_dataset_name (str): Target BigQuery dataset name.
        bq_output_table_name (str, optional): Target BigQuery table name.
        bq_location (str, optional): BigQuery location. Defaults to "US".
        store_metadata (bool, optional): Whether to store SFDC object metadata.
                                        Defaults to False.
    """

    client_info = ClientInfo(user_agent=SFDC2BQ_USER_AGENT)
    bq_client = bigquery.Client(project=bq_project_id,
                                location=bq_location,
                                client_info=client_info)
    try:
        _ = bq_client.get_dataset(bq_dataset_name)
    except NotFound:
        bq_client.create_dataset(bq_dataset_name, exists_ok=True)

    if isinstance(sfdc_auth_parameters, str):
        # sfdc_auth_parameters is a path to a Secret Manager secret
        # "projects/PROJECT_NUMBER/secrets/SECRET_NAME/versions/latest"
        sm_client = secretmanager.SecretManagerServiceClient()
        secret_response = sm_client.access_secret_version(
            name=sfdc_auth_parameters)
        secret_payload = secret_response.payload.data.decode("utf-8")
        if secret_payload.startswith("salesforce://"):
            # Airflow connections string
            secret_payload = unquote(
                secret_payload.replace("salesforce://", ""))
            username = None
            password = ""
            url_parts = secret_payload.rsplit("@", 1)
            if len(url_parts) > 1:
                parsed = urlparse(url_parts[1])
                username, password = url_parts[0].split(":", 1)
            else:
                parsed = urlparse(secret_payload)
            url_query_dict = parse_qs(parsed.query)
            auth_dict = {k: v[0] for k, v in url_query_dict.items()}
            if username:
                auth_dict["username"] = username
                auth_dict["password"] = password
            auth_dict["instance_url"] = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        else:
            # Just a json string
            auth_dict = json.loads(secret_payload)
    else:
        # This is already a dictionary
        auth_dict = sfdc_auth_parameters

    for k in list(auth_dict.keys()):
        if k != k.lower() and k != "organizationId":
            auth_dict[k.lower()] = auth_dict.pop(k)

    for k in ["consumer_key", "consumer_secret", "security_token",
              "session_id", "instance_url", "client_id", "privatekey_file"]:
        no_underscore = k.replace("_", "")
        if no_underscore in auth_dict:
            auth_dict[k] = auth_dict.pop(no_underscore)

    if "domain" in auth_dict:
        if "." not in auth_dict["domain"]:
            auth_dict["domain"] += ".my"
        elif auth_dict["domain"].endswith(".salesforce.com"):
            auth_dict["domain"] = auth_dict["domain"].replace(
                ".salesforce.com", "")

    sfdc_connection = Salesforce(**auth_dict)  # type: ignore

    sfdc2bq_replicate(simple_sf_connection=sfdc_connection,
                      api_name=api_name,
                      bq_client=bq_client,
                      project_id=bq_project_id,
                      dataset_name=bq_dataset_name,
                      output_table_name=bq_output_table_name,
                      text_encoding="utf-8",
                      include_non_standard_fields=True,
                      store_metadata=store_metadata)
