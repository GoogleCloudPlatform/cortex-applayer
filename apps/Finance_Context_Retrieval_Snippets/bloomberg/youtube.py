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

# FOR DEMO PURPOSES ONLY!

from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
import sys
import tempfile
import time
import typing
from xml.dom.minidom import parseString

import requests
from pytube import YouTube

from transcript import AudioTranscript

from googleapiclient import discovery


_DOT_KEY_NAME = ".key"

class YouTubeData:
    def __init__(self, key:str = ""):
        if not key:
            key_path = Path(__file__).parent.joinpath(_DOT_KEY_NAME)
            if not key_path.exists():
                key_path = Path(_DOT_KEY_NAME)
            if key_path.exists():
                key = key_path.read_text("utf-8").strip()
            else:
                raise ValueError("API key is empty and there is no `.key` file.")
        self.youtube = discovery.build("youtube", "v3", # type: ignore
                                  developerKey=key, cache_discovery=False)


    def get_video_info(self, url_or_id: str) -> typing.Dict:
        if url_or_id.lower().startswith("https://"):
            id = url_or_id.split("?v=")[1].split("&")[0]
        else:
            id = url_or_id.strip()
        request = self.youtube.videos().list(
                part="snippet",
                id=id)
        response = request.execute()
        return response["items"][0]["snippet"]


    def get_playlist_videos(self,
                        playlist_url_or_id: str,
                        max_video_age_hours: float = sys.float_info.max) -> (
                                typing.List[str]):
        results = []
        if playlist_url_or_id.lower().startswith("https://"):
            id = playlist_url_or_id.split("?list=")[-1].split("&")[0]
        else:
            id = playlist_url_or_id.strip()
        pageToken = ""
        while True:
            request = self.youtube.playlistItems().list(
                    part="snippet",
                    playlistId=id,
                    pageToken=pageToken)
            response = request.execute()
            items = response["items"]
            for item in items:
                details = item["snippet"]
                video_id = details["resourceId"]["videoId"]
                published_time = details["publishedAt"]
                published = datetime.strptime(published_time,
                                        "%Y-%m-%dT%H:%M:%SZ").astimezone(
                                                timezone.utc)
                age = datetime.utcnow().astimezone(
                                                timezone.utc) -  published
                if age < timedelta(hours=max_video_age_hours): # type: ignore
                    results.append(video_id)
            pageToken = response.get("nextPageToken", None)
            if not pageToken:
                break
        return results


class YoutubeTranscript:
    def __init__(self, project: str, location: str, tmp_bucket_name: str):
        self._project = project
        self._location = location
        self._bucket = tmp_bucket_name
        self.bucket_root = "youtube-transcripts"
        self.cache_path = Path(".youtube_cache").joinpath("video_transcripts")
        self.cache_path.mkdir(parents=True, exist_ok=True)


    def _convert_timedtext_xml(self, xml: str) -> str:
        dom = parseString(xml)
        body = dom.getElementsByTagName("body")[0]
        paras = body.getElementsByTagName("p")
        texts = []
        for para in paras:
            for child in para.childNodes:
                p_children = []
                if child.nodeName == 'br':
                    texts.append(" ")
                if child.nodeName == 's':
                    p_children.extend(child.childNodes)
                elif child.nodeName == '#text':
                    p_children.append(str(child.wholeText).strip())
                for p_child in p_children:
                    if isinstance(p_child, str):
                        texts.append(p_child)
                    elif p_child.nodeName == '#text':
                        texts.append(str(p_child.wholeText).strip())
        return " ".join(texts).replace("  ", " ").replace("\n\n", "\n")


    def _convert_transcribed_json(self, json_text: str) -> str:
        parts = json.loads(json_text)["results"]
        texts = []
        for part in parts:
            if ("alternatives" not in part
                  or len(part["alternatives"]) == 0
                  or "transcript" not in part["alternatives"][0]):
                continue
            transcript = part["alternatives"][0]["transcript"]
            texts.append(transcript)
        return " ".join(texts).replace("  ", " ").replace("\n\n", "\n")


    def _get_video_cache_path(self, video_id: str) -> Path:
        id_hash = hashlib.md5(video_id.encode('utf-8')).hexdigest()
        file_name = f"{id_hash}.json"
        return self.cache_path.joinpath(file_name)

    def _load_video_cache(self, video_id: str) -> typing.Optional[typing.Dict]:
        path = self._get_video_cache_path(video_id)
        if path.exists():
            return json.loads(path.read_text("utf-8"))
        else:
            return None

    def _save_video_cache(self, video_id: str, video_info: typing.Dict):
        path = self._get_video_cache_path(video_id)
        video_json = json.dumps(video_info, indent=2)
        path.write_text(video_json)

    def transcript_videos(self,
                             videos_or_playlist_url: typing.Union[
                                            typing.List[str], str],
                             max_video_age_hours: float = sys.float_info.max
                            ) -> typing.List[typing.Dict]:
        """Transcribes YouTube videos.

        Args:
            videos_or_playlist_url (typing.Union[ typing.List[str], str]):
                List of YouTube videos or playlists URLs
            max_video_age_hours (float, optional): Maximum video age in hours.
                Defaults to sys.float_info.max.

        Returns:
            typing.List[typing.Dict]: Transcribed video objects.
        """

        videos = []
        urls = (videos_or_playlist_url
                    if isinstance(videos_or_playlist_url, typing.List)
                    else [videos_or_playlist_url])

        all_videos = []
        all_videos_ids = []
        transcribed_videos = []

        logging.info("Retrieving video information.")
        data = YouTubeData()
        for url in urls:
            if "/playlist" in url:
                vids_ids = data.get_playlist_videos(url, max_video_age_hours)
                for _id in vids_ids:
                    if _id in all_videos_ids:
                        continue
                    all_videos_ids.append(_id)
                    cached = self._load_video_cache(_id)
                    if cached:
                        transcribed_videos.append(cached)
                    else:
                        v = YouTube(f"https://www.youtube.com/watch?v={_id}")
                        all_videos.append(v)
            else:
                _id = url.split("?v=")[1].split("&")[0]
                if _id in all_videos_ids:
                    continue
                all_videos_ids.append(_id)
                cached = self._load_video_cache(_id)
                if cached:
                    transcribed_videos.append(cached)
                else:
                    all_videos.append(YouTube(url))

        for vid in all_videos:
            try:
                vid.streams.first() # fetch streams
                videos.append(vid)
            except Exception as ex:
                logging.error("Video `%s` is not available.", vid.watch_url)
                logging.exception(ex, exc_info=False)

        logging.info("Processing %d videos.", len(videos))
        audio_to_transcript = {}

        for index, video in enumerate(videos):
            logging.info("Processing video `%s`.", video.watch_url)
            audio = video.streams \
                        .filter(type="audio",
                                file_extension="webm") \
                        .first()
            caption = (video.captions.get("en", None) or
                        video.captions.get("a.en", None))
            if caption:
                captionsXml = requests.get(caption.url).text # type: ignore
                captions = self._convert_timedtext_xml(captionsXml)
            else:
                captions = ""
                audio_to_transcript[index] = audio
            description = video.description.split(
                                                    "--------")[0].split(
                                                        "\n\n")[0].strip()
            publish_time_str = data.get_video_info(
                                            video.watch_url)["publishedAt"]
            published = datetime.strptime(publish_time_str,
                                    "%Y-%m-%dT%H:%M:%SZ").astimezone(
                                            timezone.utc)
            transcribed = {
                    "id": video.video_id,
                    "title": video.title,
                    "description": description,
                    "published_datetime": published.isoformat(),
                    "keywords": video.keywords,
                    "url": video.watch_url,
                    "content": captions
                }
            self._save_video_cache(video.video_id, transcribed)
            if transcribed["content"]:
                transcribed_videos.append(transcribed)

        if len(audio_to_transcript) > 0:
            logging.info("Transcribing %d videos.", len(audio_to_transcript))
            with tempfile.TemporaryDirectory() as tmp_dir:
                audio_tr = AudioTranscript(self._project, self._location)
                paths = []
                for pair in audio_to_transcript.items():
                    index = pair[0]
                    stream = pair[1]
                    name = f"{index}_{time.time_ns()}.webm"
                    stream.download(tmp_dir, name)
                    local_filepath = f"{tmp_dir}/{name}"
                    paths.append(local_filepath)
                texts = audio_tr.transcript_audio(paths, self._bucket,
                                        f"{self.bucket_root}/audio",
                                        f"{self.bucket_root}/transcripts")
                for index, t_index in enumerate(audio_to_transcript.keys()):
                    transcribed_videos[t_index]["content"] = (
                            self._convert_transcribed_json(texts[index]))
                    self._save_video_cache(transcribed_videos[t_index]["id"],
                                           transcribed_videos[t_index])
        return transcribed_videos