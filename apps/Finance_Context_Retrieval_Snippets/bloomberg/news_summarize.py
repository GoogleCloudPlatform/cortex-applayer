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

import argparse
import logging
from pathlib import Path
import sys
import typing

from google.cloud import aiplatform
from langchain.llms import VertexAI

from youtube import YoutubeTranscript

BLOOMBERG_YT_PLAYLISTS = [
    "https://www.youtube.com/playlist?list=PLGaYlBJIOoa8UZQeGopzY-m07X1Bo3NCd",
    "https://www.youtube.com/playlist?list=PLGaYlBJIOoa9DV4I6sC8R8bX4L0Jq16XZ"
]

OUTPUT_MD_FILE = Path("./summary.md")


def main(args: typing.Sequence[str]) -> int:
    logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s",
                        level=logging.INFO,
                        force=True)
    parser = argparse.ArgumentParser(description="News Summarizer.")
    parser.add_argument("--project",
                        type=str,
                        required=True)
    parser.add_argument("--location",
                        type=str,
                        required=True)
    parser.add_argument("--bucket",
                        type=str,
                        required=True)
    params = parser.parse_args(args)
    project = params.project
    location = params.location
    bucket = params.bucket

    logging.info("Getting video transcripts from YouTube.")
    yt = YoutubeTranscript(project, location, bucket)
    videos = yt.transcript_videos(BLOOMBERG_YT_PLAYLISTS, 48)

    logging.info("Summarizing transcripts.")
    aiplatform.init(project=project, location=location)
    llm = VertexAI(model_name="text-bison-32k@latest",
                   max_output_tokens=8*1024, temperature=0)

    # docs = []
    prompts = []
    for v in videos:
        output = f"Title: `{v['title']}`\n\nDescription: `{v['description']}`\n\nDate: `{v['published_datetime']}`. Keywords: `{v['keywords']}`\n\nTranscript:\n\n{v['content']}"
        prompt = f"""
        Summarize content below in 3-10 sentences.
        Make sure to keep all key dates, numbers, KPIs, names, actions and events.
        If summarizing an interview or a talk, keep most impactful quotes and statements.

        CONTENT:
        {output}
        """
        prompts.append(prompt)

    generations = llm.generate(prompts=prompts).generations
    for index, g in enumerate(generations):
        texts = [chunk.text for chunk in g]
        videos[index]["content"] = "\n".join(
            texts).replace("\n\n", "\n").strip()

    out_file = OUTPUT_MD_FILE
    out_file.unlink(True)

    vid_mds = []
    for v in videos:
        output = f"## {v['title']}\n\n{v['url']}\n\n{v['description']}\n\nDate: {v['published_datetime']}. Keywords: {v['keywords']}\n\n{v['content']}"
        vid_mds.append(output)
    out_file.write_text("\n\n".join(vid_mds), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
