"""
combined_automation.py — Run both YouTube Tracker and LinkedIn Scraper

This script acts as a single entry point for all daily automations.
"""

import logging
import sys
from pathlib import Path

# Project imports
import main as youtube_tracker
import linkedin_jobs_main as linkedin_scraper

# Logging setup for the combined run
LOG_PATH = Path(__file__).parent / "automation_combined.log"

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

def run_all():
    logger.info("=" * 60)
    logger.info("🚀 STARTING ALL DAILY AUTOMATIONS")
    logger.info("=" * 60)

    # 1. Run LinkedIn Jobs Scraper
    logger.info("\n--- STEP 1: LINKEDIN JOBS SCRAPER ---")
    try:
        linkedin_scraper.run()
    except Exception as e:
        logger.error(f"LinkedIn Scraper failed: {e}")

    # 2. Run YouTube Competitor Tracker
    logger.info("\n--- STEP 2: YOUTUBE COMPETITOR TRACKER ---")
    try:
        youtube_tracker.run()
    except Exception as e:
        logger.error(f"YouTube Tracker failed: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✅ ALL AUTOMATIONS COMPLETE")
    logger.info("=" * 60 + "\n")

if __name__ == "__main__":
    run_all()
