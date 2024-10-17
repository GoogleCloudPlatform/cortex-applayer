# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""CLI main module."""

import argparse
from concurrent import futures
import datetime
import logging
import os
import subprocess
import sys
import threading
import typing

from sfdc2bq_launcher import replicate_sfdc_object_to_bq

PARALLEL_EXECUTION_THREAD_NUM = 5  # Number of threads for replication.


def _initialize_console_logging(debug: bool = False,
                                min_level: int = logging.INFO):
    """Initializes Python root logger making sure Debug and Info
    messages go to STDOUT, while WARNING and above go to STDERR

    Args:
        debug (bool, optional): True if logging level must be set to DEBUG.
            It will be set to INFO otherwise. Defaults to False.
        min_level (int): minimal level of non-debug logging (if debug is False)
    """
    h_info_and_below = logging.StreamHandler(sys.stdout)
    h_info_and_below.setLevel(logging.DEBUG)
    h_info_and_below.addFilter(lambda record: record.levelno <= logging.INFO)
    h_warn_and_above = logging.StreamHandler(sys.stderr)
    h_warn_and_above.setLevel(logging.WARNING)

    handlers = [h_info_and_below, h_warn_and_above]
    log_format = "%(asctime)s | %(levelname)s | %(threadName)s | %(message)s"
    logging.basicConfig(format=log_format,
                        level=logging.DEBUG if debug else min_level,
                        handlers=handlers,
                        force=True)


def _run_object_replication(sfdc_auth_parameters: typing.Union[str, typing.Dict[str, str]],
                            api_name: str,
                            bq_project_id: str,
                            bq_dataset_name: str,
                            bq_output_table_name: typing.Optional[str] = None,
                            bq_location: str = "US"):
    threading.current_thread().name = f"SFDC: `{api_name}`"
    try:
        replicate_sfdc_object_to_bq(
            sfdc_auth_parameters=sfdc_auth_parameters, api_name=api_name,
            bq_project_id=bq_project_id, bq_dataset_name=bq_dataset_name,
            bq_output_table_name=bq_output_table_name,
            bq_location=bq_location)
    except:
        logging.exception(
            "Fatal error when trying to replicate %s:", api_name)
        raise


def main(args: typing.Sequence[str]) -> int:
    """CLI main function"""

    parser = argparse.ArgumentParser(
        description="Salesforce to BigQuery data transfer.")
    parser.add_argument(
        "--debug",
        help="Debugging mode.",
        action="store_true",
        default=False,
        required=False,
    )
    parser.add_argument(
        "--project",
        help="Google Cloud Project. GCloud CLI current project by default.",
        type=str,
        required=False,
        default=""
    )
    parser.add_argument(
        "--dataset",
        help="BigQuery dataset name. Dataset must exist.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--location",
        help="BigQuery location of the dataset. 'US' assumed by default.",
        type=str,
        required=False,
        default="US"
    )
    parser.add_argument(
        "--sfdc-connection-secret",
        help="Secret Manager secret name as projects/PROJECT_NUMBER/secrets/SECRET_NAME/versions/latest",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--objects-to-replicate",
        help="Comma-separated list of objects to replicate (e.g. \"Account,Opportunity,User\")",
        type=str,
        required=False,
        default="Account,Case,Contact,CurrencyType,DatedConversionRate,Event,Lead,Opportunity,RecordType,Task,User"
    )
    options, _ = parser.parse_known_args(args)

    task_count_str = os.getenv("CLOUD_RUN_TASK_COUNT", "")
    if task_count_str:
        task_count = max(int(task_count_str), 1)
        task_index = int(os.getenv("CLOUD_RUN_TASK_INDEX", "1")) - 1
    else:
        task_count = 1
        task_index = 0
    project = options.project
    if project == "<PROJECT-ID>":
        project = ""
    if project == "":
        gcloud_result = subprocess.run(("gcloud config list --format "
                                        "'value(core.project)'"),
                                       stdout=subprocess.PIPE,
                                       shell=True,
                                       check=False)
        if (gcloud_result and gcloud_result.stdout
                and gcloud_result.returncode == 0):
            project_candidate = gcloud_result.stdout.decode("utf-8").strip()
            if " " not in project_candidate:
                project = project_candidate

    options, _ = parser.parse_known_args(args)

    threading.current_thread().name = "cli"
    _initialize_console_logging(options.debug, logging.INFO)

    auth_secret = options.sfdc_connection_secret
    location = options.location
    dataset = options.dataset
    objects_str = options.objects_to_replicate
    sfdc_objects = [i.strip() for i in objects_str.split(",")]

    # Handle multi-task runs
    if task_count > 1:
        num_objects = len(sfdc_objects)
        if num_objects <= task_count:
            if task_index >= num_objects:
                logging.warning(
                    "This is an excessive task for the number of replicated SFDC objects (%d).", num_objects)
                return 0
            else:
                sfdc_objects = [sfdc_objects[task_index]]
        else:
            # Split objects between task_count tasks,
            # then pick piece number task_index.
            split_lists = [sfdc_objects[i*num_objects // task_count: (i+1)*num_objects // task_count]
                           for i in range(task_count)]
            sfdc_objects = split_lists[task_index]

    threads = []
    pool = futures.ThreadPoolExecutor(
        PARALLEL_EXECUTION_THREAD_NUM if task_count <= 1 else 1)

    logging.info(
        f"Starting replication of {len(sfdc_objects)} SFDC object(s).")
    start_time = datetime.datetime.now(datetime.timezone.utc)

    err = 0
    for obj in sfdc_objects:
        try:
            threads.append(
                pool.submit(_run_object_replication,
                            sfdc_auth_parameters=auth_secret, api_name=obj,
                            bq_project_id=project, bq_dataset_name=dataset,
                            bq_location=location))
        except Exception:
            logging.exception("Fatal error when trying to replicate %s:", obj)
            err += 1
    if len(threads) > 0:
        for f in futures.as_completed(threads):
            try:
                f.result()
            except Exception:
                err += 1

    end_time = datetime.datetime.now(datetime.timezone.utc)
    delta = (end_time - start_time).total_seconds()

    if err > 0:
        ok_reps = len(sfdc_objects) - err
        logging.warning("%d object replication(s) failed.", err)
        logging.info(
            "%d object replication(s) to `%s.%s` completed successfully in %f seconds.",
            ok_reps, project, dataset, delta)
    else:
        logging.info(
            "All %d object replication(s) to `%s.%s` completed successfully in %f seconds.",
            len(sfdc_objects), project, dataset, delta)

    return err


###############################################################
if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
