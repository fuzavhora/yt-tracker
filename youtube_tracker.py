"""
youtube_tracker.py — YouTube Data API v3 Client (Keyword Search Mode)

Instead of crawling specific channels, this searches YouTube by keyword
to discover ALL relevant videos posted in the last 24 hours.
"""

import logging
from datetime import datetime, timedelta, timezone

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class YouTubeTracker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=api_key)

    # ── Search ────────────────────────────────────────────────────────────────

    def search_recent_videos(
        self,
        keyword: str,
        hours: int = 24,
        max_results: int = 50,
    ) -> list[str]:
        """
        Search for videos matching a keyword published in the last `hours` hours.
        Returns a list of video IDs.

        Quota cost: 100 units per call.
        """
        published_after = (
            datetime.now(timezone.utc) - timedelta(hours=hours)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

        video_ids = []
        next_page_token = None

        try:
            while len(video_ids) < max_results:
                kwargs = dict(
                    part="id",
                    q=keyword,
                    type="video",
                    publishedAfter=published_after,
                    maxResults=min(50, max_results - len(video_ids)),
                    order="viewCount",   # surface most-viewed first
                    relevanceLanguage="en",
                    safeSearch="none",
                )
                if next_page_token:
                    kwargs["pageToken"] = next_page_token

                response = self.youtube.search().list(**kwargs).execute()

                for item in response.get("items", []):
                    vid_id = item.get("id", {}).get("videoId")
                    if vid_id:
                        video_ids.append(vid_id)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break

        except HttpError as e:
            logger.error(f"API error searching '{keyword}': {e}")

        logger.info(f"  Keyword '{keyword}': found {len(video_ids)} video IDs")
        return video_ids

    # ── Video Details ─────────────────────────────────────────────────────────

    def get_video_details(self, video_ids: list[str]) -> list[dict]:
        """
        Fetch snippet + statistics for a batch of video IDs (max 50 per request).
        Quota cost: 1 unit per request.
        """
        if not video_ids:
            return []

        all_videos = []

        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            try:
                response = self.youtube.videos().list(
                    part="snippet,statistics",
                    id=",".join(chunk),
                ).execute()

                for item in response.get("items", []):
                    stats   = item.get("statistics", {})
                    snippet = item.get("snippet", {})

                    published_at_str = snippet.get("publishedAt", "")
                    published_at = None
                    if published_at_str:
                        published_at = datetime.fromisoformat(
                            published_at_str.replace("Z", "+00:00")
                        )

                    thumbnails = snippet.get("thumbnails", {})
                    thumb = (
                        thumbnails.get("medium", {}).get("url", "")
                        or thumbnails.get("default", {}).get("url", "")
                    )

                    all_videos.append({
                        "video_id":     item["id"],
                        "title":        snippet.get("title", "Unknown"),
                        "channel_name": snippet.get("channelTitle", "Unknown"),
                        "channel_id":   snippet.get("channelId", ""),
                        "published_at": published_at,
                        "thumbnail":    thumb,
                        "views":        int(stats.get("viewCount",   0)),
                        "likes":        int(stats.get("likeCount",   0)),
                        "comments":     int(stats.get("commentCount", 0)),
                        "url":          f"https://www.youtube.com/watch?v={item['id']}",
                    })

            except HttpError as e:
                logger.error(f"API error fetching video details (chunk {i}): {e}")

        return all_videos

    # ── Full Pipeline ─────────────────────────────────────────────────────────

    def search_and_fetch(
        self,
        keywords: list[str],
        hours: int = 24,
        max_results_per_keyword: int = 50,
    ) -> list[dict]:
        """
        For each keyword: search for recent video IDs, then batch-fetch stats.
        Deduplicates videos that appear under multiple keywords.
        Returns a list of unique video dicts.
        """
        seen_ids: set[str] = set()
        all_ids:  list[str] = []

        for keyword in keywords:
            logger.info(f"\n🔍 Searching: '{keyword}'")
            ids = self.search_recent_videos(keyword, hours=hours, max_results=max_results_per_keyword)
            for vid_id in ids:
                if vid_id not in seen_ids:
                    seen_ids.add(vid_id)
                    all_ids.append(vid_id)

        logger.info(f"\n📦 Total unique video IDs across all keywords: {len(all_ids)}")

        if not all_ids:
            return []

        videos = self.get_video_details(all_ids)
        logger.info(f"📊 Fetched details for {len(videos)} videos")
        return videos
