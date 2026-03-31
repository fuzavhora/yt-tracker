"""
gemini_post_extractor.py — Extract structured job data from LinkedIn posts using Gemini AI

Analyzes LinkedIn hiring posts to extract:
- Job title, company name, location
- Job type (walk-in, remote, hybrid, on-site)
- Experience requirements
- Salary range (if mentioned)
- Contact/application details
- Key job requirements/skills
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class ExtractedJob:
    """Structured job data extracted from a LinkedIn post."""
    job_title: str
    company_name: str
    company_location: str
    job_type: str
    experience_required: str
    salary_range: str
    skills_required: list[str]
    contact_info: str
    application_link: str
    walk_in_drive: bool
    interview_date: str
    raw_snippet: str
    confidence_score: float

    def to_dict(self) -> dict:
        return {
            "job_title": self.job_title,
            "company_name": self.company_name,
            "company_location": self.company_location,
            "job_type": self.job_type,
            "experience_required": self.experience_required,
            "salary_range": self.salary_range,
            "skills_required": ", ".join(self.skills_required),
            "contact_info": self.contact_info,
            "application_link": self.application_link,
            "walk_in_drive": "Yes" if self.walk_in_drive else "No",
            "interview_date": self.interview_date,
            "raw_snippet": self.raw_snippet[:200],
            "confidence_score": str(self.confidence_score),
        }


SYSTEM_PROMPT = """You are an expert job posting analyzer. Your task is to extract structured job information from LinkedIn hiring posts.

Extract the following fields EXACTLY as specified:

1. job_title: The exact job role/title mentioned (e.g., "Software Developer", "Data Analyst")
2. company_name: The hiring company's name
3. company_location: City/region location of the job
4. job_type: One of: "Full-time", "Part-time", "Contract", "Internship", "Freelance", or "Not specified"
5. experience_required: Years of experience needed (e.g., "0-2 years", "3-5 years", "Fresher")
6. salary_range: Salary if mentioned (e.g., "5-8 LPA", "Not disclosed")
7. skills_required: List of key technical/soft skills mentioned
8. contact_info: Email or phone for applying
9. application_link: URL or "Not provided"
10. walk_in_drive: Boolean - true if "walk-in", "walkin", "walk in", "walk-in drive" is mentioned
11. interview_date: Date of walk-in or interview if mentioned
12. confidence_score: Float 0-1 indicating extraction confidence

Return ONLY valid JSON matching this exact schema. No markdown, no explanation."""


JOB_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "job_title": {"type": "string", "description": "Job role/title"},
        "company_name": {"type": "string", "description": "Company name"},
        "company_location": {"type": "string", "description": "Job location"},
        "job_type": {
            "type": "string",
            "enum": ["Full-time", "Part-time", "Contract", "Internship", "Freelance", "Not specified"]
        },
        "experience_required": {"type": "string", "description": "Experience needed"},
        "salary_range": {"type": "string", "description": "Salary range if mentioned"},
        "skills_required": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of required skills"
        },
        "contact_info": {"type": "string", "description": "Contact email or phone"},
        "application_link": {"type": "string", "description": "Application URL or 'Not provided'"},
        "walk_in_drive": {"type": "boolean", "description": "True if walk-in drive mentioned"},
        "interview_date": {"type": "string", "description": "Walk-in/interview date if mentioned"},
        "confidence_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence of extraction"
        }
    },
    "required": ["job_title", "company_name"]
}


class LinkedInPostJobExtractor:
    """Extract structured job data from LinkedIn posts using Gemini AI."""

    LINKEDIN_POST_URL = "https://www.linkedin.com/posts/{post_id}"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided")
        
        self.client = genai.Client(api_key=self.api_key)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def _fetch_post_content(self, post_url: str) -> str:
        """Fetch the LinkedIn post page and extract the post content."""
        try:
            resp = self.session.get(post_url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch post {post_url}: HTTP {resp.status_code}")
                return ""
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Try multiple selectors for post content
            content_selectors = [
                "div.feed-shared-update-v2__description",
                "div.update-components-text",
                "div.break-words",
                "span.break-words",
                "div.feed-shared-text",
            ]
            
            for selector in content_selectors:
                content_el = soup.select_one(selector)
                if content_el:
                    text = content_el.get_text(separator=" ", strip=True)
                    if len(text) > 50:
                        return text
            
            # Fallback: try to find any substantial text block
            main_content = soup.find("main") or soup.find("body")
            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
                if len(text) > 100:
                    return text[:5000]
            
            return ""
        except Exception as e:
            logger.error(f"Error fetching post content: {e}")
            return ""

    def _extract_with_gemini(self, text: str) -> Optional[ExtractedJob]:
        """Use Gemini to extract structured job data from post text."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"""Extract job information from this LinkedIn post:

{text}

Return ONLY JSON matching this exact schema with no additional text:
{{
    "job_title": "string",
    "company_name": "string",
    "company_location": "string",
    "job_type": "Full-time|Part-time|Contract|Internship|Freelance|Not specified",
    "experience_required": "string",
    "salary_range": "string",
    "skills_required": ["skill1", "skill2"],
    "contact_info": "string",
    "application_link": "string",
    "walk_in_drive": true|false,
    "interview_date": "string",
    "confidence_score": 0.0-1.0
}}""",
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=JOB_EXTRACTION_SCHEMA,
                )
            )
            
            if not response.text:
                return None
            
            import json
            data = json.loads(response.text)
            
            return ExtractedJob(
                job_title=data.get("job_title", "Unknown"),
                company_name=data.get("company_name", "Unknown"),
                company_location=data.get("company_location", "Not specified"),
                job_type=data.get("job_type", "Not specified"),
                experience_required=data.get("experience_required", "Not specified"),
                salary_range=data.get("salary_range", "Not disclosed"),
                skills_required=data.get("skills_required", []),
                contact_info=data.get("contact_info", "Not provided"),
                application_link=data.get("application_link", "Not provided"),
                walk_in_drive=data.get("walk_in_drive", False),
                interview_date=data.get("interview_date", "Not specified"),
                raw_snippet=text,
                confidence_score=data.get("confidence_score", 0.5),
            )
            
        except Exception as e:
            logger.error(f"Gemini extraction error: {e}")
            return None

    def extract_from_posts(self, posts: list[dict], 
                          max_posts: int = 50,
                          min_confidence: float = 0.5,
                          max_retries: int = 2,
                          retry_delay: int = 60) -> list[ExtractedJob]:
        """
        Process LinkedIn posts and extract structured job data.
        
        Args:
            posts: List of dicts with 'post_url' and 'post_snippet' keys
            max_posts: Maximum number of posts to process
            min_confidence: Minimum confidence score to include result
            max_retries: Number of retries on rate limit
            retry_delay: Seconds to wait on rate limit
        
        Returns:
            List of ExtractedJob objects
        """
        results = []
        processed = 0
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        logger.info(f"Processing {min(len(posts), max_posts)} posts with Gemini AI...")
        
        for post in posts[:max_posts]:
            post_url = post.get("post_url", "")
            snippet = post.get("post_snippet", "")
            
            if not post_url:
                continue
            
            # Try to fetch full post content, fallback to snippet
            full_content = self._fetch_post_content(post_url)
            text_to_analyze = full_content if full_content else snippet
            
            if len(text_to_analyze) < 30:
                logger.debug(f"Skipping post with insufficient content: {post_url}")
                continue
            
            logger.debug(f"Extracting job data from: {post_url[:60]}...")
            
            # Try extraction with retry logic
            extracted = None
            for attempt in range(max_retries + 1):
                try:
                    extracted = self._extract_with_gemini(text_to_analyze)
                    if extracted:
                        consecutive_errors = 0
                        break
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                        consecutive_errors += 1
                        if consecutive_errors >= max_consecutive_errors:
                            logger.warning(f"   Too many rate limit errors, stopping extraction")
                            break
                        wait_time = retry_delay * (attempt + 1)
                        logger.warning(f"   Rate limited, waiting {wait_time}s... ({attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.debug(f"   Extraction error: {e}")
                        break
            
            if extracted and extracted.confidence_score >= min_confidence:
                results.append(extracted)
                logger.info(
                    f"  ✓ Extracted: {extracted.job_title} @ {extracted.company_name} "
                    f"(confidence: {extracted.confidence_score:.2f})"
                )
            else:
                logger.debug(f"  ✗ Low confidence or failed extraction for: {post_url[:60]}")
            
            processed += 1
            
            # Rate limiting
            time.sleep(1)
        
        logger.info(f"Gemini extraction complete: {len(results)}/{processed} successful")
        return results

    def extract_from_text(self, text: str) -> Optional[ExtractedJob]:
        """Extract job data from raw text (useful for testing)."""
        return self._extract_with_gemini(text)


def create_extractor() -> LinkedInPostJobExtractor:
    """Factory function to create extractor with API key from environment."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set in environment. "
            "Get your API key from: https://aistudio.google.com/apikey"
        )
    return LinkedInPostJobExtractor(api_key=api_key)
