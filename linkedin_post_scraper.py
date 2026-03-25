"""
linkedin_post_scraper.py — Scrape LinkedIn hiring posts via Google Search

Searches Google for recent LinkedIn posts about hiring using
site:linkedin.com/posts queries. No LinkedIn login required.
"""

from __future__ import annotations

import logging
import random
import re
import time
from urllib.parse import quote_plus, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class LinkedInPostScraper:
    """Scrape LinkedIn hiring posts found via Google Search."""

    GOOGLE_SEARCH_URL = "https://www.google.com/search"

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
        time.sleep(random.uniform(3, 7))

    def _extract_real_url(self, href: str) -> str:
        """Extract the actual URL from Google's redirect wrapper."""
        if "/url?" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            return params.get("q", [href])[0]
        return href

    def _extract_author_from_url(self, url: str) -> str:
        """Extract author name from LinkedIn post URL slug."""
        # URLs look like: linkedin.com/posts/john-doe_hiring-activity-123
        try:
            path = urlparse(url).path
            # /posts/author-name_rest-of-slug
            slug = path.split("/posts/")[-1]
            author_slug = slug.split("_")[0]
            # Convert slug to readable name
            return author_slug.replace("-", " ").title()
        except Exception:
            return "Unknown"

    def search_google(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search Google for LinkedIn posts matching the query.

        Args:
            query: Search query (will be prefixed with site:linkedin.com/posts)
            max_results: Maximum results to return

        Returns:
            List of dicts with post_url, post_author, post_snippet
        """
        results = []
        full_query = f'site:linkedin.com/posts "{query}"'

        params = {
            "q": full_query,
            "num": min(max_results, 20),
            "hl": "en",
            "tbs": "qdr:d",  # Last 24 hours
        }

        try:
            self._rotate_headers()
            resp = self.session.get(
                self.GOOGLE_SEARCH_URL,
                params=params,
                timeout=15,
            )

            if resp.status_code == 429:
                logger.warning("Google rate limited, waiting 60s...")
                time.sleep(60)
                return results

            if resp.status_code != 200:
                logger.warning(f"Google search HTTP {resp.status_code}")
                return results

            soup = BeautifulSoup(resp.text, "html.parser")

            # Google search result containers
            for g in soup.select("div.g, div[data-hveid]"):
                link = g.find("a", href=True)
                if not link:
                    continue

                url = self._extract_real_url(link["href"])

                # Only keep linkedin.com/posts URLs
                if "linkedin.com/posts/" not in url:
                    continue

                # Extract snippet text
                snippet_el = g.find("div", class_="VwiC3b") or g.find("span", class_="aCOpRe")
                snippet = ""
                if snippet_el:
                    snippet = snippet_el.get_text(strip=True)

                # Extract title text
                title_el = g.find("h3")
                title = title_el.get_text(strip=True) if title_el else ""

                author = self._extract_author_from_url(url)

                # Try to extract company from snippet
                company = self._guess_company(snippet, title)

                results.append({
                    "post_url": url.split("?")[0],  # Remove tracking params
                    "post_author": author,
                    "post_title": title,
                    "post_snippet": snippet[:300],
                    "company_name": company,
                })

                if len(results) >= max_results:
                    break

        except requests.RequestException as e:
            logger.error(f"Google search error: {e}")

        return results

    def _guess_company(self, snippet: str, title: str) -> str:
        """Try to extract company name from the snippet or title."""
        text = f"{title} {snippet}"

        # Common patterns: "hiring at Company", "Company is hiring"
        patterns = [
            r"(?:hiring\s+at\s+)([A-Z][A-Za-z0-9\s&.]+?)(?:\s*[!.,\-|])",
            r"([A-Z][A-Za-z0-9\s&.]+?)\s+(?:is|are)\s+hiring",
            r"(?:join\s+)([A-Z][A-Za-z0-9\s&.]+?)(?:\s*[!.,\-|])",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 50:
                    return company

        return "N/A"

    def scrape_hiring_posts(self, keywords: list[str],
                            max_per_keyword: int = 10) -> list[dict]:
        """
        Search for LinkedIn hiring posts across multiple keywords.

        Args:
            keywords: List of search terms (e.g. ["hiring software engineer india"])
            max_per_keyword: Max results per keyword

        Returns:
            Deduplicated list of hiring post dicts
        """
        all_posts = []
        seen_urls = set()

        logger.info(f"Searching Google for LinkedIn hiring posts ({len(keywords)} keywords)...")

        for keyword in keywords:
            posts = self.search_google(
                query=keyword,
                max_results=max_per_keyword,
            )

            for post in posts:
                if post["post_url"] not in seen_urls:
                    seen_urls.add(post["post_url"])
                    all_posts.append(post)

            logger.info(f"  Found {len(posts)} posts for '{keyword}'")
            self._delay()

        logger.info(f"Total unique hiring posts found: {len(all_posts)}")
        return all_posts
