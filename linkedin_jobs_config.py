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
# Keywords designed to capture HR posts with job opportunities in last 24 hours
HIRING_POST_KEYWORDS = [
    "we are hiring india",
    "hiring software engineer india",
    "walk in drive hiring india",
    "walk-in interview today india",
    "immediate joining jobs india",
    "urgent requirement jobs india",
    "job opportunity work from home india",
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

# ─── GEMINI AI SETTINGS ───────────────────────────────────────────────────────
# Maximum posts to process with Gemini AI per run
GEMINI_MAX_POSTS_PER_RUN = 50

# Minimum confidence score (0.0-1.0) for extracted jobs
GEMINI_MIN_CONFIDENCE = 0.5

# Worksheet tab name for AI-extracted job posts
GEMINI_EXTRACTED_JOBS_WORKSHEET = "AI Extracted Jobs"

# ─── WALK-IN DRIVE KEYWORDS ───────────────────────────────────────────────────
# Keywords that indicate walk-in drives (for filtering)
WALK_IN_KEYWORDS = [
    "walk in",
    "walk-in",
    "walkin",
    "walk-in drive",
    "walk-in interview",
    "direct interview",
    "campus drive",
    "hiring drive",
]

# Hashtag mapping by category
CATEGORY_HASHTAGS = {
    "Software Development": "#softwaredeveloper #coding #programming",
    "AI/ML": "#artificialintelligence #machinelearning #ai",
    "SCADA/PLC": "#scada #plc #automation #industrialautomation",
    "Finance & Accounting": "#accounting #finance #chartered",
    "Marketing": "#digitalmarketing #marketing #socialmedia",
}
