# LinkedIn Jobs Automation — Complete Setup Guide

This guide walks you through setting up the LinkedIn Jobs Scraper automation step by step.
The automation will:
- Scrape LinkedIn for new jobs (last 24 hours) daily
- Save them to your Google Sheet automatically
- Post each job on your LinkedIn profile with a formatted description

**Total setup time: ~20 minutes**
**Cost: Completely FREE**

---

## Table of Contents

1. [Step 1: Google Cloud Service Account (for Google Sheets)](#step-1-google-cloud-service-account)
2. [Step 2: Create Google Sheet](#step-2-create-google-sheet)
3. [Step 3: LinkedIn Developer App (for auto-posting)](#step-3-linkedin-developer-app)
4. [Step 4: Generate LinkedIn Access Token](#step-4-generate-linkedin-access-token)
5. [Step 5: Configure .env File](#step-5-configure-env-file)
6. [Step 6: Test Locally](#step-6-test-locally)
7. [Step 7: Set Up GitHub Actions (Daily Automation)](#step-7-set-up-github-actions)
8. [Maintenance: Token Renewal](#maintenance-token-renewal)

---

## Step 1: Google Cloud Service Account

You need a Google Service Account to let the script write to your Google Sheet.

### 1.1 — Create or Select a Google Cloud Project

1. Open your browser and go to: **https://console.cloud.google.com/**
2. Sign in with your Google account (use the same account that owns the Google Sheet)
3. At the top-left, click the **project dropdown** (next to "Google Cloud")
4. Click **"New Project"**
   - Project name: `linkedin-jobs-automation`
   - Organization: Leave as default
   - Click **"Create"**
5. Wait for the project to be created, then **select it** from the dropdown

### 1.2 — Enable Google Sheets API

1. In the Google Cloud Console, go to the left sidebar menu
2. Click **"APIs & Services"** → **"Library"**
3. In the search bar, type: **Google Sheets API**
4. Click on **"Google Sheets API"** in the results
5. Click the blue **"Enable"** button
6. Wait for it to enable (takes a few seconds)

### 1.3 — Enable Google Drive API

1. Go back to **"APIs & Services"** → **"Library"**
2. In the search bar, type: **Google Drive API**
3. Click on **"Google Drive API"** in the results
4. Click the blue **"Enable"** button

### 1.4 — Create a Service Account

1. Go to **"APIs & Services"** → **"Credentials"** (left sidebar)
2. Click **"+ Create Credentials"** at the top
3. Select **"Service Account"**
4. Fill in:
   - Service account name: `linkedin-jobs-sheet`
   - Service account ID: (auto-filled, like `linkedin-jobs-sheet@your-project.iam.gserviceaccount.com`)
   linkedin-jobs-shee@chat-balt.iam.gserviceaccount.com
   - Description: `Writes LinkedIn job data to Google Sheets`
5. Click **"Create and Continue"**
6. Skip the "Grant this service account access" step → click **"Continue"**
7. Skip the "Grant users access" step → click **"Done"**

### 1.5 — Download the JSON Key File

1. On the **Credentials** page, find your new service account under "Service Accounts"
2. Click on the service account name (e.g., `linkedin-jobs-sheet@...`)
3. Click the **"Keys"** tab at the top
4. Click **"Add Key"** → **"Create new key"**
5. Select **"JSON"** format
6. Click **"Create"**
7. A `.json` file will download automatically — **save it safely!**
8. Rename the file to `google_credentials.json`
9. Move it to your project folder: `/Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation/`

> **IMPORTANT:** This file is already in `.gitignore` so it won't be committed to GitHub.

### 1.6 — Copy the Service Account Email

1. Open the downloaded `google_credentials.json` file
2. Find the `"client_email"` field — it looks like:
   ```
   "client_email": "linkedin-jobs-sheet@your-project.iam.gserviceaccount.com"
   ```
3. **Copy this email** — you'll need it in the next step

---

## Step 2: Create Google Sheet

### 2.1 — Create the Sheet

1. Go to: **https://sheets.google.com/**
2. Click **"+ Blank spreadsheet"** (or the big `+` button)
3. Name it exactly: **LinkedIn Jobs Tracker**
   - Click on "Untitled spreadsheet" at the top-left and type the name

### 2.2 — Share with Service Account

1. Click the **"Share"** button (top-right, green button)
2. In the "Add people" field, paste the **service account email** from Step 1.6
   (e.g., `linkedin-jobs-sheet@your-project.iam.gserviceaccount.com`)
3. Set permission to **"Editor"**
4. **Uncheck** "Notify people" (service accounts can't receive emails)
5. Click **"Share"** → confirm if prompted

> The script will auto-create the header row when it runs for the first time.

---

## Step 3: LinkedIn Developer App

You need a LinkedIn App to post jobs to your profile via the API.

### 3.1 — Create a LinkedIn Page (if you don't have one)

LinkedIn requires every app to be associated with a Company Page.

1. Go to: **https://www.linkedin.com/company/setup/new/**
2. Select **"Company"** → **"Small business"**
3. Fill in:
   - Name: Your name or brand (e.g., "Fuzail Vhora")
   - LinkedIn public URL: (auto-filled)
   - Website: Your website or GitHub URL
   - Industry: Technology
   - Company size: 1 (just you)
4. Check the verification box → click **"Create page"**

### 3.2 — Create a LinkedIn Developer App

1. Go to: **https://developer.linkedin.com/**
2. Click **"My Apps"** in the top navigation
3. Click **"Create App"**
4. Fill in:
   - **App name:** `LinkedIn Jobs Poster`
   - **LinkedIn Page:** Select the page you created in 3.1
   - **Privacy policy URL:** `https://github.com/your-username` (your GitHub profile URL is fine)
   - **App logo:** Upload any small image (required)
5. Check the legal agreement box
6. Click **"Create app"**

### 3.3 — Request API Products (Free)

1. In your app dashboard, click the **"Products"** tab
2. Find **"Share on LinkedIn"** → click **"Request access"**
   - This approves instantly (self-service)
   - Grants the `w_member_social` scope (needed for posting)
3. Find **"Sign In with LinkedIn using OpenID Connect"** → click **"Request access"**
   - This also approves instantly
   - Grants the `openid` and `profile` scopes

### 3.4 — Note Your Credentials

1. Click the **"Auth"** tab in your app
2. Copy these two values:
   - **Client ID:** (looks like `78xxxxxxxx`)
   - **Client Secret:** Click the eye icon to reveal, then copy
3. Save them — you'll add them to your `.env` file

### 3.5 — Add Redirect URL

1. Still on the **"Auth"** tab, scroll down to **"OAuth 2.0 settings"**
2. Under **"Authorized redirect URLs for your app"**, click **"Add redirect URL"**
3. Enter exactly: `http://localhost:8080/callback`
4. Click **"Update"** (or the save button)

---

## Step 4: Generate LinkedIn Access Token

This is a one-time step you run locally on your computer.

### 4.1 — Add LinkedIn Credentials to .env

Open your `.env` file and add:

```
LINKEDIN_CLIENT_ID=your_client_id_from_step_3.4
LINKEDIN_CLIENT_SECRET=your_client_secret_from_step_3.4
```

### 4.2 — Run the Auth Setup Script

Open your terminal and run:

```bash
cd /Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation
source venv/bin/activate
python linkedin_auth.py --setup
```

### 4.3 — What Happens Next

1. The script prints an authorization URL and opens your browser
2. **In your browser:** Log in to LinkedIn (if not already)
3. Click **"Allow"** to authorize the app
4. LinkedIn redirects to `localhost:8080/callback` — the script captures this
5. The terminal shows your **access token** — a long string of characters

### 4.4 — Save the Token

Copy the access token and add it to your `.env` file:

```
LINKEDIN_ACCESS_TOKEN=the_long_token_string_here
```

> **Token expires every 60 days.** Set a calendar reminder to re-run this step.
> You can validate your token anytime with: `python linkedin_auth.py --validate`

---

## Step 5: Configure .env File

Your `.env` file should now have these LinkedIn-related entries (in addition to the YouTube tracker entries):

```env
# ─── LinkedIn Jobs Scraper ───────────────────────────────────────────────────

# Option A: Path to JSON file (for local runs)
GOOGLE_SHEETS_CREDENTIALS=google_credentials.json

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=78xxxxxxxxxx
LINKEDIN_CLIENT_SECRET=xxxxxxxxxxxxxxxx
LINKEDIN_ACCESS_TOKEN=AQVxxxxxxxxxxxxxxxxxxxxxxx
```

### Verify your .env has everything:

| Variable | Where to get it | Example |
|----------|----------------|---------|
| `GOOGLE_SHEETS_CREDENTIALS` | Step 1.5 (JSON file path) | `google_credentials.json` |
| `LINKEDIN_CLIENT_ID` | Step 3.4 (Auth tab) | `78abc12345` |
| `LINKEDIN_CLIENT_SECRET` | Step 3.4 (Auth tab) | `xYz1234AbCd` |
| `LINKEDIN_ACCESS_TOKEN` | Step 4.3 (auth script output) | `AQV...very-long-string` |

---

## Step 6: Test Locally

### 6.1 — Run the Automation

```bash
cd /Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation
source venv/bin/activate
python linkedin_jobs_main.py
```

### 6.2 — Expected Output

```
============================================================
LinkedIn Jobs Scraper started — 2026-03-11 14:30:00
Keywords: 6 · Location: India · Window: last 24h
============================================================

Scraping LinkedIn jobs for 6 keywords...
  Found 15 jobs for 'Software Developer'
  Found 12 jobs for 'AI ML Engineer'
  Found 8 jobs for 'Machine Learning'
  Found 5 jobs for 'SCADA PLC Developer'
  Found 10 jobs for 'Accountant'
  Found 14 jobs for 'Digital Marketing'
Total unique jobs scraped: 58
Enriching 30 jobs with detail data...

Adding jobs to Google Sheets...
Added 58 new jobs to Google Sheets

Posting jobs to LinkedIn...
Authenticated as: Fuzail Vhora
  [1/10] Posted: Software Developer at TCS
  Waiting 60s before next post...
  [2/10] Posted: AI Engineer at Infosys
  ...
Successfully posted 10/10 jobs

============================================================
Run complete. Scraped: 58 | New in sheet: 58
============================================================
```

### 6.3 — Verify Results

1. **Google Sheet:** Open "LinkedIn Jobs Tracker" — you should see job rows with all columns filled
2. **LinkedIn Profile:** Check your LinkedIn profile — new posts should appear
3. **Log file:** Check `linkedin_jobs.log` for detailed logs

### 6.4 — Troubleshooting

| Problem | Solution |
|---------|----------|
| "Spreadsheet not found" | Make sure the sheet is named exactly **"LinkedIn Jobs Tracker"** and shared with the service account email |
| "LinkedIn token invalid" | Re-run `python linkedin_auth.py --setup` to get a new token |
| "No jobs found" | LinkedIn may be rate-limiting. Try again in 30 minutes |
| "HTTP 429" | Too many requests. The script auto-waits 30 seconds and retries |
| Import errors | Run `pip install -r requirements.txt` to install dependencies |

---

## Step 7: Set Up GitHub Actions (Daily Automation)

### 7.1 — Add GitHub Secrets

1. Go to your GitHub repository: **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** for each:

| Secret Name | Value |
|-------------|-------|
| `GOOGLE_SHEETS_CREDENTIALS` | **Entire JSON content** of `google_credentials.json` (open the file, select all, copy, paste) |
| `LINKEDIN_ACCESS_TOKEN` | The access token from Step 4 |
| `LINKEDIN_CLIENT_ID` | Your LinkedIn Client ID |
| `LINKEDIN_CLIENT_SECRET` | Your LinkedIn Client Secret |

> **For `GOOGLE_SHEETS_CREDENTIALS`:** Open `google_credentials.json` in a text editor, copy the ENTIRE content (starting with `{` and ending with `}`), and paste it as the secret value.

### 7.2 — Push Your Code

```bash
cd /Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation
git add linkedin_jobs_config.py linkedin_job_scraper.py google_sheets_client.py \
        linkedin_auth.py linkedin_poster.py linkedin_jobs_main.py \
        .github/workflows/linkedin_jobs.yml requirements.txt .env.example .gitignore
git commit -m "Add LinkedIn jobs scraper with Google Sheets and auto-posting"
git push
```

### 7.3 — Test GitHub Actions (Manual Run)

1. Go to your GitHub repository → **Actions** tab
2. Click **"Daily LinkedIn Jobs Scraper"** in the left sidebar
3. Click **"Run workflow"** → **"Run workflow"** (green button)
4. Wait for it to complete (check the green checkmark)
5. Click on the run to see logs and download the log artifact

### 7.4 — Daily Schedule

The automation runs automatically every day at **8:30 AM IST (3:00 AM UTC)**.
No further action needed — it runs on GitHub's servers for free.

---

## Maintenance: Token Renewal

LinkedIn access tokens expire every **60 days**. Here's how to renew:

### When to Renew
- Set a **calendar reminder for every 55 days**
- The script logs a warning if the token fails
- Run `python linkedin_auth.py --validate` to check if your token is still valid

### How to Renew

1. On your local machine:
   ```bash
   cd /Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation
   source venv/bin/activate
   python linkedin_auth.py --setup
   ```
2. Copy the new access token
3. Update your `.env` file with the new token
4. Update the GitHub Secret:
   - Repository → Settings → Secrets → `LINKEDIN_ACCESS_TOKEN` → Update

---

## How It All Works (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions (Daily 8:30 AM IST)        │
│                         OR                                  │
│                   Manual: python linkedin_jobs_main.py       │
└────────────────────────────┬────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   1. SCRAPE     │
                    │   LinkedIn      │
                    │   Public Jobs   │
                    │   (No login)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  2. DEDUPLICATE │
                    │  Remove jobs    │
                    │  already in     │
                    │  Google Sheet   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  3. SAVE TO     │
                    │  Google Sheets  │
                    │  (via API)      │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  4. POST TO     │
                    │  LinkedIn       │
                    │  (via API)      │
                    │  Max 10/day     │
                    └─────────────────┘
```

### Files Overview

| File | What it does |
|------|-------------|
| `linkedin_jobs_main.py` | Main script — runs the full pipeline |
| `linkedin_jobs_config.py` | Settings — keywords, location, hashtags |
| `linkedin_job_scraper.py` | Scrapes LinkedIn public job pages |
| `google_sheets_client.py` | Reads/writes to Google Sheets |
| `linkedin_poster.py` | Posts jobs to your LinkedIn profile |
| `linkedin_auth.py` | Helper to generate LinkedIn OAuth token |
| `.github/workflows/linkedin_jobs.yml` | GitHub Actions daily schedule |

---

## Customisation

### Change Job Keywords
Edit `linkedin_jobs_config.py`:
```python
JOB_KEYWORDS = [
    "Software Developer",
    "AI ML Engineer",
    "Your Custom Keyword",
]
```

### Change Location
Edit `linkedin_jobs_config.py`:
```python
LOCATION = "Mumbai, India"  # or "Remote", "USA", etc.
```

### Change Schedule Time
Edit `.github/workflows/linkedin_jobs.yml`:
```yaml
schedule:
  - cron: '30 4 * * *'  # 10:00 AM IST (4:30 AM UTC)
```
Use https://crontab.guru/ to generate cron expressions.

### Change Max Posts Per Day
Edit `linkedin_jobs_config.py`:
```python
MAX_POSTS_PER_RUN = 5  # Reduce to post fewer jobs
```
