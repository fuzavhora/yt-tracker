"""
linkedin_poster.py — Post jobs to LinkedIn via API

Uses the LinkedIn ugcPosts API with w_member_social scope to create
text posts on the authenticated user's LinkedIn profile.
"""

import logging
import time

import requests

from linkedin_jobs_config import CATEGORY_HASHTAGS

logger = logging.getLogger(__name__)


class LinkedInPoster:
    """Post job listings to a LinkedIn profile."""

    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
    UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        self._person_urn = None

    def get_person_urn(self) -> str:
        """Fetch the authenticated user's person URN."""
        if self._person_urn:
            return self._person_urn

        resp = requests.get(
            self.USERINFO_URL,
            headers={"Authorization": f"Bearer {self.access_token}"},
            timeout=10,
        )

        if resp.status_code != 200:
            logger.error(f"Failed to get user info: HTTP {resp.status_code}")
            logger.error("Your LinkedIn access token may be expired.")
            logger.error("Re-run: python linkedin_auth.py --setup")
            raise RuntimeError("LinkedIn token invalid or expired")

        user_data = resp.json()
        sub = user_data.get("sub")
        self._person_urn = f"urn:li:person:{sub}"
        logger.info(f"Authenticated as: {user_data.get('name', 'Unknown')}")
        return self._person_urn

    def compose_post_text(self, job: dict) -> str:
        """
        Create a formatted LinkedIn post for a single job listing.

        Args:
            job: Dict with job_title, company_name, company_location,
                 job_category, job_url

        Returns:
            Formatted post text
        """
        category = job.get("job_category", "")
        hashtags = CATEGORY_HASHTAGS.get(category, "#jobs")

        text = (
            f"Hiring Alert! {job['job_title']} at {job['company_name']}\n"
            f"\n"
            f"Company: {job['company_name']}\n"
            f"Location: {job.get('company_location', 'India')}\n"
            f"Category: {category}\n"
            f"\n"
            f"Apply here: {job.get('job_url', '')}\n"
            f"\n"
            f"#hiring {hashtags} #jobs #india #careers"
        )
        return text

    def compose_combined_post(self, jobs: list) -> str:
        """
        Create a single LinkedIn post listing all hiring companies.

        Groups jobs by company and fits within LinkedIn's 3000 char limit.

        Args:
            jobs: List of job dicts

        Returns:
            Formatted combined post text
        """
        from datetime import datetime

        MAX_CHARS = 2900  # Buffer below LinkedIn's 3000 limit

        today = datetime.now().strftime("%d %b %Y")

        # Collect unique company names (preserve insertion order)
        companies = dict.fromkeys(
            job.get("company_name", "Unknown") for job in jobs
        )

        # Collect unique hashtags
        all_hashtags = set()
        for job in jobs:
            category = job.get("job_category", "")
            tags = CATEGORY_HASHTAGS.get(category, "")
            for tag in tags.split():
                all_hashtags.add(tag)

        hashtag_line = f"\n#hiring #jobs #india #careers {' '.join(sorted(all_hashtags))}"

        # Build header and footer CTA
        header = (
            f"These giants are hiring today! ({today})\n"
            f"Go apply now before it's too late!\n"
            f"\n"
        )

        footer = (
            f"\n"
            f"Want the full list with apply links? Comment \"JOB\" and follow me.\n"
            f"I'll share the Google Sheet link with you!\n"
        )

        # Add companies one by one until we hit the char limit
        company_lines = []
        remaining = MAX_CHARS - len(header) - len(hashtag_line)

        for company in companies:
            line = f"- {company}\n"
            if remaining - len(line) < 50:  # Reserve space for "and X more"
                left = len(companies) - len(company_lines)
                company_lines.append(f"...and {left} more companies!\n")
                break
            company_lines.append(line)
            remaining -= len(line)

        return header + "".join(company_lines) + hashtag_line

    def create_post(self, text: str) -> bool:
        """
        Publish a text post to LinkedIn.

        Args:
            text: The post content

        Returns:
            True if posted successfully, False otherwise
        """
        author_urn = self.get_person_urn()

        payload = {
            "author": author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        try:
            resp = requests.post(
                self.UGC_POSTS_URL,
                headers=self.headers,
                json=payload,
                timeout=15,
            )

            if resp.status_code in (200, 201):
                logger.info("Post published successfully")
                return True

            logger.warning(
                f"LinkedIn post failed: HTTP {resp.status_code} — {resp.text}"
            )
            return False

        except requests.RequestException as e:
            logger.error(f"Error posting to LinkedIn: {e}")
            return False

    def post_jobs(self, jobs: list, max_posts: int = 10,
                  delay_seconds: int = 60) -> list:
        """
        Post all jobs as a single combined LinkedIn post.

        Args:
            jobs: List of job dicts
            max_posts: Maximum number of jobs to include in the post
            delay_seconds: (unused, kept for backwards compatibility)

        Returns:
            List of successfully posted job dicts
        """
        jobs_to_post = jobs[:max_posts]

        if not jobs_to_post:
            logger.info("No jobs to post to LinkedIn")
            return []

        logger.info(
            f"Creating combined LinkedIn post with {len(jobs_to_post)} jobs..."
        )

        text = self.compose_combined_post(jobs_to_post)
        success = self.create_post(text)

        if success:
            logger.info(
                f"Combined post published with {len(jobs_to_post)} jobs"
            )
            return jobs_to_post
        else:
            logger.warning("Failed to publish combined post")
            return []
