"""
analyzer.py — Outperformance Detection (24-hour window, absolute thresholds)

Since we're discovering videos via keyword search (no fixed channels),
we use absolute thresholds instead of per-channel averages.
"""

import logging
from config import THRESHOLDS

logger = logging.getLogger(__name__)


def calculate_engagement_rate(views: int, likes: int, comments: int) -> float:
    """Engagement rate as a percentage: (likes + comments) / views * 100."""
    if views == 0:
        return 0.0
    return round((likes + comments) / views * 100, 2)


def is_outperforming(video: dict) -> tuple[bool, list[str]]:
    """
    Check if a single video meets outperformance criteria.

    Returns (True, [reasons]) or (False, []).

    A video is outperforming if it meets ANY of:
      1. Views >= absolute_views_high  (strong viral signal)
      2. Views >= absolute_views_mid   AND engagement >= threshold
      3. Engagement rate >= threshold  AND views >= minimum
    """
    views    = video["views"]
    likes    = video["likes"]
    comments = video["comments"]

    views_high  = THRESHOLDS["absolute_views_high"]
    views_mid   = THRESHOLDS["absolute_views_mid"]
    eng_thresh  = THRESHOLDS["engagement_rate_threshold_pct"]
    min_views   = THRESHOLDS["minimum_views"]

    # Hard floor — ignore noise
    if views < min_views:
        return False, []

    eng_rate = calculate_engagement_rate(views, likes, comments)
    reasons  = []

    # Criterion 1: Raw viral reach
    if views >= views_high:
        reasons.append(f"🚀 {views:,} views in 24h (>{views_high:,} threshold)")

    # Criterion 2: Solid views + high engagement
    if views >= views_mid and eng_rate >= eng_thresh:
        if not reasons:  # avoid duplicate if already caught above
            reasons.append(f"📈 {views:,} views with {eng_rate}% engagement")

    # Criterion 3: Pure engagement excellence (+ minimum view floor)
    if eng_rate >= eng_thresh and not reasons:
        reasons.append(f"💬 {eng_rate}% engagement rate (>{eng_thresh}% threshold)")

    return bool(reasons), reasons


def analyze(videos: list[dict]) -> list[dict]:
    """
    Filter the full list of discovered videos down to outperformers.

    Returns list of outperforming video dicts (sorted by views desc).
    """
    outperformers = []

    for video in videos:
        flagged, reasons = is_outperforming(video)
        if not flagged:
            continue

        eng_rate = calculate_engagement_rate(
            video["views"], video["likes"], video["comments"]
        )

        published_str = ""
        if video.get("published_at"):
            published_str = video["published_at"].strftime("%b %d, %Y · %H:%M UTC")

        outperformers.append({
            **video,
            "engagement_rate": eng_rate,
            "published_at":    published_str,
            "reasons":         reasons,
        })

    # Sort by views descending
    outperformers.sort(key=lambda v: v["views"], reverse=True)
    logger.info(f"🔥 {len(outperformers)} outperforming videos found out of {len(videos)} analyzed")
    return outperformers
