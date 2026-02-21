"""
config.py — YouTube Competitor Tracker Configuration

The tracker searches YouTube by keyword (no fixed channel list).
Edit SEARCH_KEYWORDS and THRESHOLDS to tune behaviour.
"""

# ─── SEARCH KEYWORDS ─────────────────────────────────────────────────────────
# These are used to find recent videos in the AI/automation niche.
# Each keyword = 1 search API call (100 quota units each).
# 10 keywords = ~1,000 units/day (well within the 10,000 free quota).

SEARCH_KEYWORDS = [
    "AI tools 2025",
    "AI automation tutorial",
    "AI agents explained",
    "no code AI",
    "ChatGPT tutorial 2025",
    "AI business ideas",
    "n8n automation workflow",
    "make.com automation",
    "AI startup ideas",
    "artificial intelligence news 2025",
]

# ─── SEARCH SETTINGS ─────────────────────────────────────────────────────────
# Max results per keyword search (1–50, YouTube API limit = 50)
MAX_RESULTS_PER_KEYWORD = 50

# How many hours back to look for videos (24 = last 24 hours)
LOOKBACK_HOURS = 24

# ─── OUTPERFORMANCE THRESHOLDS (absolute — for 24-hour window) ───────────────
# A video posted in the last 24 hours is "outperforming" if it meets ANY of:
THRESHOLDS = {
    # Views in 24 hours — very strong signal of virality
    "absolute_views_high": 20_000,    # Definitely viral for 24h

    # Moderate views but high engagement
    "absolute_views_mid": 5_000,      # Combined with engagement below

    # Engagement rate % = (likes + comments) / views × 100
    "engagement_rate_threshold_pct": 5.0,

    # Minimum views to even be considered (filter spam/low-quality)
    "minimum_views": 1_000,
}

# ─── YOUR CHANNEL INFO (for email footer / reference) ────────────────────────
YOUR_CHANNEL_HANDLE = "@fmv"
YOUR_CHANNEL_URL    = "https://www.youtube.com/@thesoloentrepreneur07"
