# Bloomberg News Summarization

## DISCLAIMER

This code is for demonstration purposes only. It is not intended to be used in production.
You are expected to have all required licensing and permissions to use content that this code fetches.
This is not an official and/or recommended approach to work with YouTube content.

## How to use

Requires an API key for YouTube Data API v3 (https://pantheon.corp.google.com/apis/api/youtube.googleapis.com/credentials)
saved as `.key` file.

YouTubeData class also accepts key as an argument.

* Run `news_summarize.py`
> python news_summarize.py --project <gcp_project_name> --location <gcp_region> --bucket <gcs_bucket_name>
> * gcp_project_name: GCP region for Vertex AI, Speech-to-Text API and YouTube API
> * gcp_region: GCP region for Vertex AI, Speech-to-Text API
> * gcs_bucket_name: GCS bucket name for Speech-to-Text usage

* Inspect `summary.md` produced by the code.
