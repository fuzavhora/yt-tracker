"""
google_sheets_client.py — Google Sheets integration via gspread

Manages reading/writing job data to a Google Sheet using a Service Account.
Handles deduplication and tracks which jobs have been posted to LinkedIn.
"""

import json
import logging
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

HEADERS = [
    "Date Scraped",
    "Job Role",
    "Company Name",
    "Post Sender Name",
    "Company Website",
    "Company Location",
    "Job Category",
    "Job URL",
    "Posted To LinkedIn",
]


class GoogleSheetsClient:
    """Read/write job data to Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    def __init__(self, credentials_json: str, sheet_name: str, worksheet_name: str):
        """
        Initialise the Google Sheets client.

        Args:
            credentials_json: Either a file path to the service account JSON,
                              or the raw JSON string (for GitHub Actions secrets)
            sheet_name: Name of the Google Sheet spreadsheet
            worksheet_name: Name of the worksheet tab within the spreadsheet
        """
        creds = self._load_credentials(credentials_json)
        self.gc = gspread.authorize(creds)

        try:
            self.spreadsheet = self.gc.open(sheet_name)
        except gspread.SpreadsheetNotFound:
            logger.error(
                f"Spreadsheet '{sheet_name}' not found. "
                "Make sure it exists and is shared with the service account email."
            )
            raise

        try:
            self.worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            logger.info(f"Worksheet '{worksheet_name}' not found, creating it...")
            self.worksheet = self.spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=len(HEADERS)
            )

        self._ensure_headers()

    def _load_credentials(self, credentials_json: str) -> Credentials:
        """Load credentials from file path or raw JSON string."""
        try:
            # Try as file path first
            creds_data = json.loads(open(credentials_json).read())
        except (FileNotFoundError, OSError):
            # Treat as raw JSON string
            creds_data = json.loads(credentials_json)

        return Credentials.from_service_account_info(creds_data, scopes=self.SCOPES)

    def _ensure_headers(self):
        """Create the header row if the sheet is empty."""
        first_row = self.worksheet.row_values(1)
        if not first_row or first_row != HEADERS:
            self.worksheet.update("A1", [HEADERS])
            logger.info("Sheet headers initialised.")

    def get_existing_job_urls(self) -> set:
        """Return set of job URLs already in the sheet for deduplication."""
        try:
            url_col_index = HEADERS.index("Job URL") + 1  # 1-indexed
            urls = self.worksheet.col_values(url_col_index)
            return set(urls[1:])  # Skip header row
        except Exception as e:
            logger.warning(f"Could not read existing URLs: {e}")
            return set()

    def append_jobs(self, jobs: list) -> int:
        """
        Append new jobs to the sheet, skipping duplicates.

        Args:
            jobs: List of job dicts from the scraper

        Returns:
            Number of new jobs added
        """
        existing_urls = self.get_existing_job_urls()
        today = datetime.now().strftime("%Y-%m-%d")

        new_rows = []
        for job in jobs:
            if job.get("job_url") in existing_urls:
                continue

            row = [
                today,
                job.get("job_title", "N/A"),
                job.get("company_name", "N/A"),
                job.get("post_sender_name", "N/A"),
                job.get("company_website", "N/A"),
                job.get("company_location", "N/A"),
                job.get("job_category", "N/A"),
                job.get("job_url", ""),
                "No",  # Posted To LinkedIn
            ]
            new_rows.append(row)

        if new_rows:
            self.worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
            logger.info(f"Added {len(new_rows)} new jobs to Google Sheets")
        else:
            logger.info("No new jobs to add (all duplicates)")

        return len(new_rows)

    def get_unposted_jobs(self) -> list:
        """
        Return jobs that haven't been posted to LinkedIn yet.

        Returns:
            List of dicts with job data for unposted jobs
        """
        all_records = self.worksheet.get_all_records()
        unposted = []

        for record in all_records:
            posted_status = str(record.get("Posted To LinkedIn", "")).strip().lower()
            if posted_status not in ("yes", "true"):
                unposted.append({
                    "job_title": record.get("Job Role", ""),
                    "company_name": record.get("Company Name", ""),
                    "post_sender_name": record.get("Post Sender Name", ""),
                    "company_website": record.get("Company Website", ""),
                    "company_location": record.get("Company Location", ""),
                    "job_category": record.get("Job Category", ""),
                    "job_url": record.get("Job URL", ""),
                })

        logger.info(f"Found {len(unposted)} unposted jobs")
        return unposted

    def mark_as_posted(self, job_url: str):
        """Mark a job as posted to LinkedIn by setting the column to 'Yes'."""
        try:
            url_col_index = HEADERS.index("Job URL") + 1
            posted_col_index = HEADERS.index("Posted To LinkedIn") + 1

            cell = self.worksheet.find(job_url, in_column=url_col_index)
            if cell:
                self.worksheet.update_cell(cell.row, posted_col_index, "Yes")
        except Exception as e:
            logger.warning(f"Could not mark job as posted: {e}")
