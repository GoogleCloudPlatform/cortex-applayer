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

import typing

from google.cloud.speech_v2 import SpeechClient
from google.cloud.speech_v2.types import cloud_speech
from google.cloud import storage

MAX_FILES_PER_OPERATION = 15


class AudioTranscript:
    def __init__(self, project: str, location: str):
        self._project = project
        self._location = location
        self.storage_client = storage.Client(project=project)
        self.speech_client = SpeechClient()
        self.regional_recognizer_name = f"projects/{project}/locations/{location}/recognizers/_"
        self.global_recognizer_name = f"projects/{project}/locations/global/recognizers/_"

    def transcript_audio(self, local_file_paths: typing.Iterable[str],
                        workspace_bucket_name: str,
                        workspace_tmp_path: str,
                        transcript_output_path) -> typing.List[str]:
        result = []
        local_file_paths = list(local_file_paths)
        for i in range(0, len(local_file_paths), MAX_FILES_PER_OPERATION):
            chunk = local_file_paths[i:i + MAX_FILES_PER_OPERATION]
            res_chunk = self._transcript_audio(chunk,
                                               workspace_bucket_name,
                                               workspace_tmp_path,
                                               transcript_output_path)
            result.extend(res_chunk)
        return result


    def _transcript_audio(self, local_file_paths: typing.Iterable[str],
                        workspace_bucket_name: str,
                        workspace_tmp_path: str,
                        transcript_output_path) -> typing.List[str]:

        workspace = f"gs://{workspace_bucket_name}/{transcript_output_path}"

        gcs_paths = [self._upload_to_gcs(workspace_bucket_name,
                                workspace_tmp_path,
                                file_path) for file_path in local_file_paths]

        config = cloud_speech.RecognitionConfig(
        auto_decoding_config={},
        model="long",
        language_codes=["en-US"],
        features=cloud_speech.RecognitionFeatures(
                                profanity_filter=True,
                                enable_word_time_offsets=True,
                                enable_word_confidence=True,
                                enable_automatic_punctuation=True)
        )

        output_config = cloud_speech.RecognitionOutputConfig(
        gcs_output_config=cloud_speech.GcsOutputConfig(
            uri=workspace),
        )

        files = [cloud_speech.BatchRecognizeFileMetadata(
            uri=gcs_uri) for gcs_uri in gcs_paths]

        request = cloud_speech.BatchRecognizeRequest(
            recognizer=self.global_recognizer_name,
            config=config,
            files=files,
            recognition_output_config=output_config
        )
        operation = self.speech_client.batch_recognize(request=request)
        results = dict(operation.result().results) # type: ignore
        jsons = []
        bucket = self.storage_client.bucket(workspace_bucket_name)
        prefix_len = len(f"gs://{workspace_bucket_name}/")
        for gsc_path in gcs_paths:
            transcript_json_gs_url = results[gsc_path].uri
            blob = bucket.get_blob(transcript_json_gs_url[prefix_len:])
            jsons.append(blob.download_as_text()) # type: ignore
            blob.delete() # type: ignore
        for gcs_uri in gcs_paths:
            blob = bucket.get_blob(gcs_uri[prefix_len:])
            blob.delete() # type: ignore
        return jsons


    def _upload_to_gcs(self, bucket_name: str, gcs_path: str, local_filepath: str):
        if not gcs_path or gcs_path == "/":
            gcs_path = ""
        elif not gcs_path.endswith("/"):
            gcs_path += "/"

        gcs_blob_name  = gcs_path + local_filepath.split('/')[-1]
        gcs_filepath   = 'gs://{}/{}'.format(bucket_name, gcs_blob_name)

        storage_client = storage.Client()
        gcs_bucket     = storage_client.get_bucket(bucket_name)
        gcs_blob       = gcs_bucket.blob(gcs_blob_name)
        gcs_blob.upload_from_filename(local_filepath)
        return gcs_filepath

