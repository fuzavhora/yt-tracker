"""
main.py — YouTube Competitor Tracker Orchestrator

Searches YouTube by AI-related keywords for videos posted in the last 24 hours,
identifies outperforming ones, and sends an HTML email report.

Run manually: python main.py
Scheduled:    cron runs this at 2pm daily (see setup_cron.sh)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# ── Load .env first ───────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

# ── Project imports ───────────────────────────────────────────────────────────
from config import SEARCH_KEYWORDS, LOOKBACK_HOURS, MAX_RESULTS_PER_KEYWORD
from youtube_tracker import YouTubeTracker
from analyzer import analyze
from email_reporter import EmailReporter

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_PATH = Path(__file__).parent / "tracker.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def validate_env() -> bool:
    required = [
        "YOUTUBE_API_KEY", "SMTP_HOST", "SMTP_PORT",
        "SMTP_USER", "SMTP_PASSWORD", "RECIPIENT_EMAIL",
    ]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        logger.error(f"Missing environment variables: {', '.join(missing)}")
        logger.error("Fill in your .env file (copy from .env.example).")
        return False
    return True


def run():
    logger.info("=" * 60)
    logger.info(f"YouTube Tracker started — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Mode: Keyword search · Window: last {LOOKBACK_HOURS}h")
    logger.info("=" * 60)

    if not validate_env():
        sys.exit(1)

    tracker  = YouTubeTracker(api_key=os.environ["YOUTUBE_API_KEY"])
    reporter = EmailReporter()

    # ── 1. Search all keywords, collect unique videos ─────────────────────────
    logger.info(f"\n📡 Searching {len(SEARCH_KEYWORDS)} keywords (last {LOOKBACK_HOURS}h)...")
    all_videos = tracker.search_and_fetch(
        keywords=SEARCH_KEYWORDS,
        hours=LOOKBACK_HOURS,
        max_results_per_keyword=MAX_RESULTS_PER_KEYWORD,
    )

    logger.info(f"\n📦 Total unique videos found: {len(all_videos)}")

    if not all_videos:
        logger.warning("No videos found — check your API key and keyword list.")
        # Still send a check-in email so you know the tracker ran
        reporter.send_report([])
        return

    # ── 2. Identify outperformers ─────────────────────────────────────────────
    logger.info("\n🔍 Analyzing for outperforming videos...")
    outperformers = analyze(all_videos)

    logger.info(f"\n🔥 Top outperformers:")
    for v in outperformers[:10]:
        logger.info(
            f"  • [{v['channel_name']}] {v['title'][:55]}... "
            f"| {v['views']:,} views | {v['engagement_rate']}% eng"
        )

    # ── 3. Send email report ──────────────────────────────────────────────────
    logger.info(f"\n📧 Sending report to {os.environ['RECIPIENT_EMAIL']}...")
    success = reporter.send_report(
        outperformers,
        videos_scanned=len(all_videos),
        keywords_count=len(SEARCH_KEYWORDS),
    )

    if success:
        logger.info("✅ Email sent successfully!")
    else:
        logger.error("❌ Email failed — see logs for details")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("Run complete.")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    run()
