"""
linkedin_post_scraper.py — Scrape LinkedIn hiring posts via DuckDuckGo Search

Searches DuckDuckGo for recent LinkedIn posts about hiring using
site:linkedin.com/posts queries. No LinkedIn login required.
Includes 24-hour time filtering and timestamp extraction.
"""

from __future__ import annotations

import logging
import random
import re
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CUTOFF_HOURS = 24

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class LinkedInPostScraper:
    """Scrape LinkedIn hiring posts found via DuckDuckGo Search."""

    DUCK_SEARCH_URL = "https://html.duckduckgo.com/html/"
    DUCK_API_URL = "https://api.duckduckgo.com/"

    def __init__(self):
        self.session = requests.Session()
        self._rotate_headers()

    def _rotate_headers(self):
        """Set random user-agent and standard headers for DuckDuckGo."""
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        })

    def _delay(self):
        """Random delay between requests to avoid rate limiting."""
        time.sleep(random.uniform(8, 15))

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

    def _extract_time_from_snippet(self, snippet: str, result_text: str) -> datetime | None:
        """
        Try to extract timestamp from Google search snippet.
        Google often shows "2 hours ago", "1 day ago", "Mar 15, 2025", etc.
        Returns None if no valid time found.
        """
        text = f"{snippet} {result_text}".lower()
        now = datetime.now()
        
        time_patterns = [
            # "X hours/minutes/seconds ago"
            (r'(\d+)\s*hour[s]?\s*ago', lambda m: now - timedelta(hours=int(m.group(1)))),
            (r'(\d+)\s*min[s]?\s*ago', lambda m: now - timedelta(minutes=int(m.group(1)))),
            (r'(\d+)\s*sec[s]?\s*ago', lambda m: now - timedelta(seconds=int(m.group(1)))),
            (r'(\d+)\s*day[s]?\s*ago', lambda m: now - timedelta(days=int(m.group(1)))),
            
            # Relative: "yesterday"
            (r'yesterday', lambda m: now - timedelta(days=1)),
            
            # Date formats
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[.\s]*(\d{1,2}),?\s*(\d{4})', 
             lambda m: self._parse_month_date(m)),
            (r'(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[.\s]*(\d{4})', 
             lambda m: self._parse_date_month(m)),
        ]
        
        for pattern, extractor in time_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return extractor(match)
                except Exception:
                    continue
        return None
    
    def _parse_month_date(self, match) -> datetime:
        """Parse 'Mar 15, 2025' format."""
        month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                     'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        month = month_map.get(match.group(1).lower()[:3], 1)
        day = int(match.group(2))
        year = int(match.group(3))
        return datetime(year, month, day)
    
    def _parse_date_month(self, match) -> datetime:
        """Parse '15 Mar 2025' format."""
        month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                     'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
        day = int(match.group(1))
        month = month_map.get(match.group(2).lower()[:3], 1)
        year = int(match.group(3))
        return datetime(year, month, day)
    
    def _is_within_24_hours(self, post_time: datetime | None) -> bool:
        """Check if post was within the last 24 hours."""
        if post_time is None:
            return True  # If we can't determine time, include it (Google already filtered)
        cutoff = datetime.now() - timedelta(hours=CUTOFF_HOURS)
        return post_time >= cutoff

    def search_duckduckgo(self, query: str, max_results: int = 10) -> list[dict]:
        """
        Search DuckDuckGo for LinkedIn posts matching the query.

        Args:
            query: Search query (will be prefixed with site:linkedin.com/posts)
            max_results: Maximum results to return

        Returns:
            List of dicts with post_url, post_author, post_snippet, post_time
        """
        results = []
        full_query = f'site:linkedin.com/posts "{query}"'
        
        logger.info(f"   Searching: '{query}'")

        params = {
            "q": full_query,
        }

        retry_count = 0
        max_retries = 3
        
        while retry_count <= max_retries:
            try:
                self._rotate_headers()
                resp = self.session.get(
                    self.DUCK_SEARCH_URL,
                    params=params,
                    timeout=20,
                )

                if resp.status_code == 202:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.info(f"   Processing... retry {retry_count}/{max_retries} after 10s...")
                        time.sleep(10)
                        continue
                    else:
                        logger.warning(f"   Still processing, skipping '{query}'")
                        return results
                
                if resp.status_code == 429:
                    retry_count += 1
                    if retry_count <= max_retries:
                        logger.warning(f"   Rate limited, retry {retry_count}/{max_retries} after 30s...")
                        time.sleep(30)
                        continue
                    else:
                        logger.warning(f"   Max retries reached, skipping '{query}'")
                        return results

                if resp.status_code != 200:
                    logger.warning(f"   HTTP {resp.status_code} for '{query}'")
                    return results

                soup = BeautifulSoup(resp.text, "html.parser")

                # DuckDuckGo result containers - try multiple selectors
                result_elements = (
                    soup.select("div.result") or 
                    soup.select("div[data-result]") or
                    soup.select(".result")
                )

                for result in result_elements:
                    link = result.find("a", href=True)
                    if not link:
                        continue

                    url = link.get("href", "")
                    
                    # Skip if not a LinkedIn post URL
                    if "linkedin.com/posts/" not in url:
                        continue

                    # Extract title
                    title = link.get_text(strip=True) or ""
                    
                    # Extract snippet
                    snippet_el = result.find("a", class_="result__snippet")
                    if not snippet_el:
                        snippet_el = result.find("div", class_="result__snippet")
                    if not snippet_el:
                        snippet_el = result.find("p")
                    
                    snippet = snippet_el.get_text(strip=True) if snippet_el else ""

                    # Extract time info from snippet
                    post_time = self._extract_time_from_snippet(snippet, "")
                    
                    # Double-check 24 hour filter
                    if not self._is_within_24_hours(post_time):
                        continue

                    author = self._extract_author_from_url(url)
                    company = self._guess_company(snippet, title)

                    results.append({
                        "post_url": url.split("?")[0],
                        "post_author": author,
                        "post_title": title,
                        "post_snippet": snippet[:300] if snippet else "",
                        "company_name": company,
                        "post_time": post_time.isoformat() if post_time else None,
                    })

                    if len(results) >= max_results:
                        break

                logger.info(f"   Found {len(results)} posts for '{query}'")
                break  # Success, exit retry loop

            except requests.RequestException as e:
                logger.error(f"   Search error for '{query}': {e}")
                return results

        return results
    
    # Alias for backwards compatibility
    def search_google(self, query: str, max_results: int = 10) -> list[dict]:
        """Alias for search_duckduckgo for backwards compatibility."""
        return self.search_duckduckgo(query, max_results)

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
        total_found = 0

        logger.info(f"Searching DuckDuckGo for LinkedIn hiring posts ({len(keywords)} keywords)...")
        logger.info(f"Time filter: Last {CUTOFF_HOURS} hours only")

        for keyword in keywords:
            posts = self.search_duckduckgo(
                query=keyword,
                max_results=max_per_keyword,
            )

            new_posts = 0
            for post in posts:
                if post["post_url"] not in seen_urls:
                    seen_urls.add(post["post_url"])
                    all_posts.append(post)
                    new_posts += 1

            total_found += len(posts)
            self._delay()

        logger.info(f"Total unique hiring posts (last 24h): {len(all_posts)}")
        
        # Log walk-in drive posts separately
        walk_in_posts = [p for p in all_posts if "walk" in p.get("post_snippet", "").lower() or "walk" in p.get("post_title", "").lower()]
        if walk_in_posts:
            logger.info(f"   🔍 Found {len(walk_in_posts)} walk-in drive related posts!")
        
        return all_posts
