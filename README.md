# YouTube Competitor Tracker 🎬📊

> **Runs daily at 2pm · Monitors competitor channels · Sends you an HTML email report**

An automated Python script that uses the YouTube Data API v3 to track competitor channels in the AI/automation niche, identifies outperforming videos, and emails you a beautiful daily report.

---

## 📁 Project Structure

```
Automation/
├── main.py              ← Entry point (run this)
├── config.py            ← Competitors list + thresholds (edit here)
├── youtube_tracker.py   ← YouTube API client
├── analyzer.py          ← Outperformance logic
├── email_reporter.py    ← HTML email builder + SMTP sender
├── requirements.txt     ← Python dependencies
├── .env                 ← Your secrets (create from .env.example)
├── .env.example         ← Secrets template
├── setup_cron.sh        ← One-click Hostinger deploy script
└── tracker.log          ← Auto-generated logs
```

---

## ⚡ Quick Start (Local Test)

### 1. Install dependencies

```bash
cd /path/to/Automation
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Get a YouTube Data API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Search for **"YouTube Data API v3"** → Enable it
4. Go to **Credentials** → **Create Credentials** → **API Key**
5. Copy the key

> **Free quota:** 10,000 units/day — enough for ~15 competitors checked daily.

### 3. Set up Gmail App Password (for sending email)

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Select App: **Mail** → Device: **Other** → name it "YouTubeTracker"
3. Copy the 16-character app password (NOT your Gmail login password)

### 4. Create your `.env` file

```bash
cp .env.example .env
nano .env   # or open in any editor
```

Fill in:
```env
YOUTUBE_API_KEY=AIzaSy...your_key_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
RECIPIENT_EMAIL=your@email.com
```

### 5. Customize competitors & thresholds (optional)

Open `config.py` and edit:

```python
COMPETITOR_CHANNELS = [
    {"name": "Matt Wolfe", "id": "UCKkl0T1_MHY7HuoQaJjsRHg"},
    # Add more...
]

THRESHOLDS = {
    "views_vs_average_multiplier": 2.0,   # 2x channel avg = outperforming
    "absolute_views_threshold": 50_000,    # 50k+ views always flags it
    "engagement_rate_threshold_pct": 5.0,  # 5%+ engagement flags it
    "lookback_days": 30,                   # Analyze last 30 days of videos
    "minimum_views": 5_000,                # Ignore videos with < 5k views
}
```

**How to find a YouTube channel ID:**
- Visit their channel → View Page Source → Ctrl+F for `"channelId"`
- Or use: [commentpicker.com/youtube-channel-id.php](https://commentpicker.com/youtube-channel-id.php)

### 6. Run it!

```bash
source venv/bin/activate
python main.py
```

You'll see live logs and receive an email within ~1-2 minutes.

---

## 🖥️ Deploy on Hostinger KVM 2

### Step 1: SSH into your server

```bash
ssh root@your.hostinger.ip.address
```

### Step 2: Upload the project

**Option A — Git (recommended):**
```bash
# On your server:
git clone https://github.com/yourusername/your-repo.git /opt/yt-tracker
cd /opt/yt-tracker
```

**Option B — SCP from your Mac:**
```bash
# On your Mac (runs locally):
scp -r /Users/fuzailmukhtyarahmeadvhora/Development/Projects/Automation root@YOUR_SERVER_IP:/opt/yt-tracker
```

### Step 3: Create `.env` on the server

```bash
cd /opt/yt-tracker
cp .env.example .env
nano .env    # Fill in your API key + email credentials
```

### Step 4: Run the deploy script

```bash
chmod +x setup_cron.sh
./setup_cron.sh
```

This will:
- ✅ Install Python3 & pip (if missing)
- ✅ Create a virtual environment
- ✅ Install all dependencies
- ✅ Set server timezone
- ✅ Register the cron job at **2:00pm daily**
- ✅ Configure log rotation (14 days)

> **Edit timezone in `setup_cron.sh`:** Change `TIMEZONE="Asia/Kolkata"` to your preferred zone.  
> Common values: `UTC`, `Asia/Kolkata`, `America/New_York`, `Europe/London`

### Step 5: Verify the cron is registered

```bash
crontab -l
```

Should show:
```
# YouTube Competitor Tracker — Daily at 14:00
0 14 * * * /opt/yt-tracker/venv/bin/python /opt/yt-tracker/main.py >> /opt/yt-tracker/tracker.log 2>&1
```

---

## 🔧 Useful Commands (on server)

```bash
# Run manually right now
/opt/yt-tracker/venv/bin/python /opt/yt-tracker/main.py

# Watch live logs
tail -f /opt/yt-tracker/tracker.log

# Edit competitor list
nano /opt/yt-tracker/config.py

# Edit .env secrets
nano /opt/yt-tracker/.env

# View cron jobs
crontab -l

# Remove cron job
crontab -e   # Then delete the tracker line
```

---

## 📧 What the Email Looks Like

Every day at 2pm you'll receive:

- **Subject:** `🔥 5 Outperforming Competitor Videos — February 20, 2026`
- **Content:** Beautifully formatted HTML email with:
  - Video thumbnail, title (clickable), channel name
  - Views, likes, comments, engagement rate, publish date
  - Colour-coded reason badges (why it was flagged)
  - Grouped by channel

If no videos outperform that day: `✅ Competitor Tracker — No outperformers today`

---

## 📊 How "Outperforming" is Defined

A video is flagged if it meets **any** of:

| Criterion | Default Value | Meaning |
|-----------|--------------|---------|
| **Relative views** | 2× channel avg | Double the channel's 30-day average |
| **Absolute views** | 50,000 | Raw viral threshold |
| **Engagement rate** | 5% | (likes + comments) / views |

All thresholds are configurable in `config.py` → `THRESHOLDS`.

---

## 🔑 API Quota

YouTube Data API v3 free tier = **10,000 units/day**.

| Operation | Units |
|-----------|-------|
| `channels().list()` | 1 unit/request |
| `playlistItems().list()` | 1 unit/request |
| `videos().list()` | 1 unit/request |

**Estimated usage:** ~15 competitors × ~3 requests each = **~45 units/day** → well within the free limit. ✅

---

## 📝 Competitor Channel IDs (Pre-configured)

| Channel | ID |
|---------|----|
| Matt Wolfe | `UCKkl0T1_MHY7HuoQaJjsRHg` |
| Liam Ottley | `UC4xNJMTcLqVUGlC_3GXioqQ` |
| The AI Grid | `UCt7kuuFpFmEqiAOrrDaGotg` |
| Greg Isenberg | `UCfRzMbCJoJbdWXdFJnZdFHg` |
| Nick Saraev | `UCsKDEUDG3Dxn2ZfnCWJBMhQ` |
| Riley Brown | `UCRatSIHQlCFvTkPsULlYt0g` |
| Santrel Media | `UCWqr2tH3dPBMcIejjXYPBkA` |
| AI Explained | `UCNJ1Ymd5yFuUPtn21xtRbbw` |
| David Ondrej | `UCIaH-OAMBpBxfNBXY5JhkdA` |
| Tina Huang | `UC2UXDak6o7rBm23x3jGpu3A` |
| Corbin Brown | `UCo8bcnLyZH8tBIH9V1mLgqQ` |
| Prompt Engineering | `UCF0pVplsI8R5kcAqgtoRqoA` |
| The Futur | `UC-b3c7kxa5vU-bnmaROgvog` |
| Iman Gadzhi | `UCMOqf9DFk0PREcl2nzRltnA` |
| YCombinator | `UCcefcZRL2oaA_uBNeo5UNqg` |

> ⚠️ Some channel IDs may need verification — if a channel returns no videos, double-check its ID using the method above.
