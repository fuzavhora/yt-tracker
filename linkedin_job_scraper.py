"""
linkedin_job_scraper.py — Scrape public LinkedIn job listings

Uses requests + BeautifulSoup to parse LinkedIn's public job search pages.
No login or API key required. Respects rate limits with random delays.
"""

from __future__ import annotations

import logging
import random
import time
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Rotate user-agents to reduce chance of blocking
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class LinkedInJobScraper:
    """Scrape job listings from LinkedIn's public job search pages."""

    BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    def __init__(self):
        self.session = requests.Session()
        self._rotate_headers()

    def _rotate_headers(self):
        """Set random user-agent and standard headers."""
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        })

    def _delay(self):
        """Random delay between requests to avoid rate limiting."""
        time.sleep(random.uniform(2, 5))

    def search_jobs(self, keyword: str, location: str, category: str,
                    hours: int = 24, max_results: int = 25) -> list:
        """
        Scrape public LinkedIn job listings for a keyword + location.

        Args:
            keyword: Job search term (e.g. "Software Developer")
            location: Location filter (e.g. "India")
            category: Job category label for tagging
            hours: Only return jobs posted within this many hours
            max_results: Maximum number of jobs to return

        Returns:
            List of job dicts with keys: job_title, company_name,
            company_location, job_url, job_id, job_category, posted_date
        """
        jobs = []
        start = 0
        page_size = 25

        time_filter = f"r{hours * 3600}"  # r86400 = last 24 hours

        while len(jobs) < max_results:
            params = {
                "keywords": keyword,
                "location": location,
                "f_TPR": time_filter,
                "start": start,
                "position": 1,
                "pageNum": 0,
            }

            try:
                self._rotate_headers()
                resp = self.session.get(self.BASE_URL, params=params, timeout=15)

                if resp.status_code == 429:
                    logger.warning(f"Rate limited on '{keyword}', waiting 30s...")
                    time.sleep(30)
                    continue

                if resp.status_code != 200:
                    logger.warning(
                        f"HTTP {resp.status_code} for keyword '{keyword}'. "
                        "LinkedIn might be blocking this request (especially from GitHub Actions). "
                        "Try running locally or using a proxy."
                    )
                    break

                soup = BeautifulSoup(resp.text, "html.parser")
                cards = soup.find_all("div", class_="base-card")

                if not cards:
                    break

                for card in cards:
                    job = self._parse_card(card, category)
                    if job and job["job_id"] not in {j["job_id"] for j in jobs}:
                        jobs.append(job)

                    if len(jobs) >= max_results:
                        break

                start += page_size
                self._delay()

            except requests.RequestException as e:
                logger.error(f"Request error for '{keyword}': {e}")
                break

        logger.info(f"  Found {len(jobs)} jobs for '{keyword}'")
        return jobs

    def _parse_card(self, card, category: str) -> dict | None:
        """Extract job data from a single search result card."""
        try:
            # Job title
            title_el = card.find("h3", class_="base-search-card__title")
            job_title = title_el.get_text(strip=True) if title_el else None

            # Company name
            company_el = card.find("h4", class_="base-search-card__subtitle")
            company_name = company_el.get_text(strip=True) if company_el else "N/A"

            # Location
            location_el = card.find("span", class_="job-search-card__location")
            company_location = location_el.get_text(strip=True) if location_el else "N/A"

            # Job URL and ID
            link_el = card.find("a", class_="base-card__full-link")
            if not link_el:
                link_el = card.find("a", href=True)

            job_url = ""
            job_id = ""
            if link_el and link_el.get("href"):
                job_url = link_el["href"].split("?")[0]  # Remove tracking params
                # Extract job ID from URL like /jobs/view/1234567890/
                parts = job_url.rstrip("/").split("/")
                job_id = parts[-1] if parts else ""

            # Posted date
            time_el = card.find("time")
            posted_date = ""
            if time_el:
                posted_date = time_el.get("datetime", time_el.get_text(strip=True))

            if not job_title or not job_id:
                return None

            return {
                "job_title": job_title,
                "company_name": company_name,
                "company_location": company_location,
                "job_url": job_url,
                "job_id": job_id,
                "job_category": category,
                "posted_date": posted_date,
                "post_sender_name": "N/A",  # Will be enriched from detail page
                "company_website": "N/A",   # Will be enriched from detail page
            }

        except Exception as e:
            logger.debug(f"Error parsing card: {e}")
            return None

    def enrich_job_details(self, job: dict) -> dict:
        """
        Fetch the individual job detail page to extract additional info
        like recruiter name and company website.
        """
        if not job.get("job_id"):
            return job

        try:
            url = self.DETAIL_URL.format(job_id=job["job_id"])
            self._rotate_headers()
            resp = self.session.get(url, timeout=15)

            if resp.status_code != 200:
                return job

            soup = BeautifulSoup(resp.text, "html.parser")

            # Try to find poster/recruiter name
            poster_el = soup.find("a", class_="message-the-recruiter__cta")
            if poster_el:
                job["post_sender_name"] = poster_el.get_text(strip=True)

            # Try to find company website from the company link
            company_link = soup.find("a", class_="topcard__org-name-link")
            if company_link and company_link.get("href"):
                job["company_website"] = company_link["href"].split("?")[0]

            self._delay()

        except requests.RequestException as e:
            logger.debug(f"Error enriching job {job['job_id']}: {e}")

        return job

    def scrape_all_keywords(self, keywords: list, location: str,
                            category_map: dict, hours: int = 24,
                            max_per_keyword: int = 25,
                            enrich: bool = True) -> list:
        """
        Scrape jobs for all keywords, deduplicate, and optionally enrich.

        Args:
            keywords: List of search terms
            location: Location filter
            category_map: Keyword -> category name mapping
            hours: Lookback window in hours
            max_per_keyword: Max jobs per keyword
            enrich: Whether to fetch detail pages for extra info

        Returns:
            Deduplicated list of job dicts
        """
        all_jobs = []
        seen_ids = set()

        logger.info(f"Scraping {len(keywords)} keywords for '{location}' (last {hours}h)...")

        for keyword in keywords:
            category = category_map.get(keyword, keyword)
            jobs = self.search_jobs(
                keyword=keyword,
                location=location,
                category=category,
                hours=hours,
                max_results=max_per_keyword,
            )

            for job in jobs:
                if job["job_id"] not in seen_ids:
                    seen_ids.add(job["job_id"])
                    all_jobs.append(job)

            self._delay()

        logger.info(f"Total unique jobs scraped: {len(all_jobs)}")

        # Enrich top jobs with detail page data (limit to avoid too many requests)
        if enrich and all_jobs:
            enrich_count = min(len(all_jobs), 30)  # Max 30 detail fetches
            logger.info(f"Enriching {enrich_count} jobs with detail data...")
            for i in range(enrich_count):
                all_jobs[i] = self.enrich_job_details(all_jobs[i])

        return all_jobs
