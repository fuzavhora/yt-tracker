"""
linkedin_jobs_config.py — LinkedIn Job Scraper Configuration

Edit JOB_KEYWORDS, LOCATION, and other settings to customise behaviour.
"""

# ─── JOB SEARCH KEYWORDS ────────────────────────────────────────────────────
# Each keyword generates a separate scrape query on LinkedIn public jobs.
JOB_KEYWORDS = [
    "Software Developer",
    "AI ML Engineer",
    "Machine Learning",
    "SCADA PLC Developer",
    "Accountant",
    "Digital Marketing",
]

# ─── LOCATION ────────────────────────────────────────────────────────────────
LOCATION = "India"

# ─── SEARCH SETTINGS ─────────────────────────────────────────────────────────
# How many hours back to look for jobs (24 = last 24 hours)
LOOKBACK_HOURS = 24

# Maximum number of jobs to scrape per keyword
MAX_JOBS_PER_KEYWORD = 25

# ─── GOOGLE SHEET SETTINGS ───────────────────────────────────────────────────
GOOGLE_SHEET_NAME = "LinkedIn Jobs Tracker"
WORKSHEET_NAME = "Jobs"

# ─── CATEGORY MAPPING ────────────────────────────────────────────────────────
# Maps each keyword to a human-readable job category for the sheet
KEYWORD_CATEGORY_MAP = {
    "Software Developer": "Software Development",
    "AI ML Engineer": "AI/ML",
    "Machine Learning": "AI/ML",
    "SCADA PLC Developer": "SCADA/PLC",
    "Accountant": "Finance & Accounting",
    "Digital Marketing": "Marketing",
}

# ─── HIRING POSTS (Google Search for LinkedIn posts) ────────────────────────
# Search queries to find hiring-related LinkedIn posts via Google
HIRING_POST_KEYWORDS = [
    "hiring software engineer india",
    "hiring AI ML engineer india",
    "hiring accountant india",
    "hiring digital marketing india",
    "we are hiring india",
]

# Maximum hiring posts to scrape per keyword
MAX_HIRING_POSTS_PER_KEYWORD = 10

# Worksheet tab for hiring posts in Google Sheets
HIRING_POSTS_WORKSHEET = "Hiring Posts"

# ─── LINKEDIN POSTING SETTINGS ───────────────────────────────────────────────
# Maximum number of jobs to include in the combined LinkedIn post
MAX_POSTS_PER_RUN = 150

# Delay in seconds between LinkedIn posts
POST_DELAY_SECONDS = 60

# Hashtag mapping by category
CATEGORY_HASHTAGS = {
    "Software Development": "#softwaredeveloper #coding #programming",
    "AI/ML": "#artificialintelligence #machinelearning #ai",
    "SCADA/PLC": "#scada #plc #automation #industrialautomation",
    "Finance & Accounting": "#accounting #finance #chartered",
    "Marketing": "#digitalmarketing #marketing #socialmedia",
}
