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
    GEMINI_MAX_POSTS_PER_RUN, GEMINI_MIN_CONFIDENCE,
    GEMINI_EXTRACTED_JOBS_WORKSHEET,
)
from linkedin_job_scraper import LinkedInJobScraper
from linkedin_post_scraper import LinkedInPostScraper
from google_sheets_client import GoogleSheetsClient
from linkedin_poster import LinkedInPoster

try:
    from gemini_post_extractor import LinkedInPostJobExtractor, create_extractor
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

_gemini_enabled = GEMINI_AVAILABLE

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

    # Check Gemini availability
    gemini_enabled = _gemini_enabled
    if gemini_enabled and not os.environ.get("GEMINI_API_KEY"):
        logger.warning("GEMINI_API_KEY not set — skipping AI extraction from posts.")
        gemini_enabled = False

    # ── 1. Scrape LinkedIn hiring posts FIRST (higher priority) ─────────────────
    hiring_posts = []
    gemini_extracted_jobs = []
    
    try:
        logger.info(f"\n🔍 Step 1: Searching LinkedIn hiring posts ({len(HIRING_POST_KEYWORDS)} keywords)...")
        post_scraper = LinkedInPostScraper()
        hiring_posts = post_scraper.scrape_hiring_posts(
            keywords=HIRING_POST_KEYWORDS,
            max_per_keyword=MAX_HIRING_POSTS_PER_KEYWORD,
        )
        logger.info(f"   Found {len(hiring_posts)} hiring posts from HR profiles")
        
        # Log post samples
        if hiring_posts:
            logger.info("   Sample posts:")
            for p in hiring_posts[:3]:
                logger.info(f"   - {p.get('post_title', 'N/A')[:60]}")
    except Exception as e:
        logger.error(f"   Hiring posts error: {e}")

    # ── 2. Extract structured jobs from posts using Gemini AI ──────────────────
    if gemini_enabled and hiring_posts:
        logger.info(f"\n🤖 Step 2: Extracting jobs from posts using Gemini AI...")
        try:
            extractor = create_extractor()
            gemini_extracted_jobs = extractor.extract_from_posts(
                posts=hiring_posts,
                max_posts=GEMINI_MAX_POSTS_PER_RUN,
                min_confidence=GEMINI_MIN_CONFIDENCE,
            )
            
            # Add source URL to each job
            for i, job in enumerate(gemini_extracted_jobs):
                if i < len(hiring_posts):
                    job["source_url"] = hiring_posts[i].get("post_url", "")
            
            logger.info(f"   Extracted {len(gemini_extracted_jobs)} structured jobs")
            
            walk_in_drives = [j for j in gemini_extracted_jobs if j.walk_in_drive]
            if walk_in_drives:
                logger.info(f"   🔔 Found {len(walk_in_drives)} WALK-IN DRIVE opportunities!")
                
        except Exception as e:
            logger.error(f"   Gemini extraction error: {e}")

    # ── 3. Scrape LinkedIn jobs from job board ─────────────────────────────────
    logger.info(f"\n📋 Step 3: Scraping LinkedIn job board for {len(JOB_KEYWORDS)} keywords...")

    scraper = LinkedInJobScraper()
    all_jobs = scraper.scrape_all_keywords(
        keywords=JOB_KEYWORDS,
        location=LOCATION,
        category_map=KEYWORD_CATEGORY_MAP,
        hours=LOOKBACK_HOURS,
        max_per_keyword=MAX_JOBS_PER_KEYWORD,
        enrich=True,
    )

    logger.info(f"   Total unique jobs scraped: {len(all_jobs)}")
    if all_jobs:
        for job in all_jobs[:3]:
            logger.info(f"   - {job['job_title'][:40]} @ {job['company_name'][:25]}")

    if not all_jobs and not hiring_posts:
        logger.info("No new jobs or hiring posts found. Exiting.")
        return

    # ── 4. Add to Google Sheets ────────────────────────────────────────────────
    new_count = 0
    new_posts_count = 0
    new_gemini_count = 0
    if features["sheets"]:
        logger.info("\n📊 Step 4: Adding data to Google Sheets...")
        try:
            sheets = GoogleSheetsClient(
                credentials_json=os.environ["GOOGLE_SHEETS_CREDENTIALS"],
                sheet_name=GOOGLE_SHEET_NAME,
                worksheet_name=WORKSHEET_NAME,
            )
            new_count = sheets.append_jobs(all_jobs)
            logger.info(f"   Jobs added: {new_count}")

            # Save hiring posts to separate tab
            if hiring_posts:
                new_posts_count = sheets.append_hiring_posts(
                    hiring_posts, HIRING_POSTS_WORKSHEET
                )
                logger.info(f"   Hiring posts added: {new_posts_count}")
            
            # Save Gemini extracted jobs
            if gemini_extracted_jobs:
                new_gemini_count = sheets.append_gemini_jobs(
                    gemini_extracted_jobs, GEMINI_EXTRACTED_JOBS_WORKSHEET
                )
                logger.info(f"   AI-extracted jobs added: {new_gemini_count}")

        except Exception as e:
            logger.error(f"   Google Sheets error: {e}")
            sheets = None
    else:
        sheets = None

    # ── 5. Post to LinkedIn ────────────────────────────────────────────────────
    if features["posting"]:
        logger.info("\n📤 Step 5: Posting jobs to LinkedIn...")
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

            logger.info(f"   Posted {len(posted)} items to LinkedIn")

        except Exception as e:
            logger.error(f"   LinkedIn posting error: {e}")

    # ── Summary ────────────────────────────────────────────────────────────────
    walk_in_count = len([j for j in gemini_extracted_jobs if j.walk_in_drive]) if gemini_extracted_jobs else 0
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 RUN SUMMARY")
    logger.info(f"  • LinkedIn Jobs scraped: {len(all_jobs)}")
    logger.info(f"  • HR Hiring posts found: {len(hiring_posts)}")
    logger.info(f"  • AI-extracted jobs: {len(gemini_extracted_jobs)}")
    logger.info(f"  • Walk-in drives: {walk_in_count}")
    logger.info(f"  • Jobs added to sheet: {new_count}")
    logger.info(f"  • Hiring posts in sheet: {new_posts_count}")
    logger.info(f"  • AI jobs in sheet: {new_gemini_count}")
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    run()
