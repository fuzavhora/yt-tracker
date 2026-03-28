"""
linkedin_jobs_main.py — LinkedIn Job Scraper + Sheets + Poster Orchestrator

Scrapes LinkedIn for recent job postings, logs them in Google Sheets,
and auto-posts each job to the user's LinkedIn profile.

Run manually:  python linkedin_jobs_main.py
Scheduled:     GitHub Actions runs this daily at 8:30 AM IST
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
from linkedin_jobs_config import (
    JOB_KEYWORDS, LOCATION, LOOKBACK_HOURS, MAX_JOBS_PER_KEYWORD,
    KEYWORD_CATEGORY_MAP, GOOGLE_SHEET_NAME, WORKSHEET_NAME,
    MAX_POSTS_PER_RUN, POST_DELAY_SECONDS,
    HIRING_POST_KEYWORDS, MAX_HIRING_POSTS_PER_KEYWORD,
    HIRING_POSTS_WORKSHEET,
)
from linkedin_job_scraper import LinkedInJobScraper
from linkedin_post_scraper import LinkedInPostScraper
from google_sheets_client import GoogleSheetsClient
from linkedin_poster import LinkedInPoster

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_PATH = Path(__file__).parent / "linkedin_jobs.log"

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


def validate_env() -> dict:
    """
    Check required environment variables. Returns a dict indicating
    which features are available.
    """
    features = {"sheets": False, "posting": False}

    sheets_creds = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if sheets_creds:
        features["sheets"] = True
    else:
        logger.warning(
            "GOOGLE_SHEETS_CREDENTIALS not set — skipping Google Sheets."
        )

    linkedin_token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    if linkedin_token:
        features["posting"] = True
    else:
        logger.warning(
            "LINKEDIN_ACCESS_TOKEN not set — skipping LinkedIn posting."
        )

    return features


def run():
    logger.info("=" * 60)
    logger.info(
        f"LinkedIn Jobs Scraper started — "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(
        f"Keywords: {len(JOB_KEYWORDS)} · Location: {LOCATION} · "
        f"Window: last {LOOKBACK_HOURS}h"
    )
    logger.info("=" * 60)

    features = validate_env()

    # ── 1. Scrape LinkedIn jobs ────────────────────────────────────────────────
    logger.info(f"\nScraping LinkedIn jobs for {len(JOB_KEYWORDS)} keywords...")

    scraper = LinkedInJobScraper()
    all_jobs = scraper.scrape_all_keywords(
        keywords=JOB_KEYWORDS,
        location=LOCATION,
        category_map=KEYWORD_CATEGORY_MAP,
        hours=LOOKBACK_HOURS,
        max_per_keyword=MAX_JOBS_PER_KEYWORD,
        enrich=True,
    )

    logger.info(f"\nTotal unique jobs scraped: {len(all_jobs)}")

    # Log summary
    if all_jobs:
        for job in all_jobs[:5]:
            logger.info(
                f"  {job['job_title'][:40]} | {job['company_name'][:25]} | "
                f"{job['company_location'][:20]}"
            )
        if len(all_jobs) > 5:
            logger.info(f"  ... and {len(all_jobs) - 5} more")

    # ── 2. Scrape LinkedIn hiring posts via Google ─────────────────────────────
    hiring_posts = []
    try:
        logger.info(f"\nSearching for LinkedIn hiring posts ({len(HIRING_POST_KEYWORDS)} keywords)...")
        post_scraper = LinkedInPostScraper()
        hiring_posts = post_scraper.scrape_hiring_posts(
            keywords=HIRING_POST_KEYWORDS,
            max_per_keyword=MAX_HIRING_POSTS_PER_KEYWORD,
        )
        logger.info(f"Found {len(hiring_posts)} unique hiring posts")
    except Exception as e:
        logger.error(f"Hiring posts scraping error: {e}")

    if not all_jobs and not hiring_posts:
        logger.info("No new jobs or hiring posts found. Exiting.")
        return

    # ── 3. Add to Google Sheets ────────────────────────────────────────────────
    new_count = 0
    new_posts_count = 0
    if features["sheets"]:
        logger.info("\nAdding jobs to Google Sheets...")
        try:
            sheets = GoogleSheetsClient(
                credentials_json=os.environ["GOOGLE_SHEETS_CREDENTIALS"],
                sheet_name=GOOGLE_SHEET_NAME,
                worksheet_name=WORKSHEET_NAME,
            )
            new_count = sheets.append_jobs(all_jobs)
            logger.info(f"Added {new_count} new jobs to Google Sheets")

            # Save hiring posts to separate tab
            if hiring_posts:
                new_posts_count = sheets.append_hiring_posts(
                    hiring_posts, HIRING_POSTS_WORKSHEET
                )
                logger.info(f"Added {new_posts_count} hiring posts to Google Sheets")

        except Exception as e:
            logger.error(f"Google Sheets error: {e}")
            sheets = None
    else:
        sheets = None

    # ── 4. Post to LinkedIn ────────────────────────────────────────────────────
    if features["posting"]:
        logger.info("\nPosting jobs to LinkedIn...")
        try:
            poster = LinkedInPoster(
                access_token=os.environ["LINKEDIN_ACCESS_TOKEN"]
            )

            # Get unposted jobs from sheet, or use scraped jobs
            if sheets:
                jobs_to_post = sheets.get_unposted_jobs()
            else:
                jobs_to_post = all_jobs

            posted = poster.post_jobs(
                jobs=jobs_to_post,
                hiring_posts=hiring_posts,
                max_posts=MAX_POSTS_PER_RUN,
                delay_seconds=POST_DELAY_SECONDS,
            )

            # Mark posted jobs in the sheet (batch to avoid rate limits)
            if sheets:
                posted_urls = [job.get("job_url", "") for job in posted if job.get("job_url")]
                if posted_urls:
                    sheets.batch_mark_as_posted(posted_urls)

            logger.info(f"Posted {len(posted)} jobs to LinkedIn")

        except Exception as e:
            logger.error(f"LinkedIn posting error: {e}")

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("\n" + "=" * 60)
    logger.info(f"Run complete. Scraped: {len(all_jobs)} | "
                f"Hiring posts: {len(hiring_posts)} | "
                f"New in sheet: {new_count}")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    run()
