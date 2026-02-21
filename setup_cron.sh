#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup_cron.sh — Deploy YouTube Competitor Tracker on Hostinger KVM 2
# 
# Usage (on your Hostinger server via SSH):
#   chmod +x setup_cron.sh
#   ./setup_cron.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit on any error

# ── Config ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
PYTHON_BIN="python3"
CRON_HOUR=14       # 2pm
CRON_MINUTE=0
TIMEZONE="Asia/Kolkata"   # ← CHANGE THIS to your timezone (e.g., UTC, Asia/Kolkata, America/New_York)
LOG_FILE="$SCRIPT_DIR/tracker.log"

echo "═══════════════════════════════════════════════════"
echo "  YouTube Competitor Tracker — Hostinger Setup"
echo "═══════════════════════════════════════════════════"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────────────────
echo "▶ Checking Python installation..."
if ! command -v $PYTHON_BIN &> /dev/null; then
    echo "  Python3 not found. Installing..."
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$($PYTHON_BIN --version 2>&1)
echo "  ✓ $PYTHON_VERSION"

# ── Step 2: Create virtual environment ───────────────────────────────────────
echo ""
echo "▶ Creating virtual environment at $VENV_DIR..."
$PYTHON_BIN -m venv "$VENV_DIR"
echo "  ✓ Virtual environment created"

# ── Step 3: Install dependencies ─────────────────────────────────────────────
echo ""
echo "▶ Installing dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "  ✓ Dependencies installed"

# ── Step 4: Validate .env exists ─────────────────────────────────────────────
echo ""
echo "▶ Checking .env file..."
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo ""
    echo "  ⚠️  .env file not found!"
    echo "  Please create it from the template:"
    echo ""
    echo "    cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    echo "    nano $SCRIPT_DIR/.env"
    echo ""
    echo "  Then re-run this script."
    exit 1
fi
echo "  ✓ .env file found"

# ── Step 5: Set timezone on server ───────────────────────────────────────────
echo ""
echo "▶ Setting server timezone to $TIMEZONE..."
if command -v timedatectl &> /dev/null; then
    sudo timedatectl set-timezone "$TIMEZONE" 2>/dev/null || echo "  ⚠ Could not set timezone automatically, set it manually with: sudo timedatectl set-timezone $TIMEZONE"
else
    echo "  ⚠ timedatectl not available. Verify your server timezone is correct."
fi
echo "  ✓ Timezone: $(date +%Z) ($(date '+%Y-%m-%d %H:%M:%S'))"

# ── Step 6: Test the script before scheduling ─────────────────────────────────
echo ""
echo "▶ Running a quick validation test..."
"$VENV_DIR/bin/python" -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from dotenv import load_dotenv
load_dotenv('$SCRIPT_DIR/.env')
import os
required = ['YOUTUBE_API_KEY', 'SMTP_HOST', 'SMTP_PORT', 'SMTP_USER', 'SMTP_PASSWORD', 'RECIPIENT_EMAIL']
missing = [k for k in required if not os.environ.get(k)]
if missing:
    print('  ✗ Missing env vars:', ', '.join(missing))
    sys.exit(1)
print('  ✓ All environment variables found')
print('  ✓ Will send report to:', os.environ['RECIPIENT_EMAIL'])
"

# ── Step 7: Register cron job ─────────────────────────────────────────────────
echo ""
echo "▶ Registering cron job (runs daily at ${CRON_HOUR}:$(printf '%02d' $CRON_MINUTE))..."

CRON_CMD="$CRON_MINUTE $CRON_HOUR * * * $VENV_DIR/bin/python $SCRIPT_DIR/main.py >> $LOG_FILE 2>&1"
CRON_COMMENT="# YouTube Competitor Tracker — Daily at ${CRON_HOUR}:$(printf '%02d' $CRON_MINUTE)"

# Remove any existing tracker cron entry, then add fresh one
(crontab -l 2>/dev/null | grep -v "YouTube Competitor Tracker" | grep -v "main.py" ; echo "$CRON_COMMENT"; echo "$CRON_CMD") | crontab -

echo "  ✓ Cron job registered:"
echo "    $CRON_CMD"

# ── Step 8: Setup log rotation ────────────────────────────────────────────────
echo ""
echo "▶ Configuring log rotation..."
if command -v logrotate &> /dev/null; then
    LOGROTATE_CONF="/etc/logrotate.d/yt_competitor_tracker"
    sudo bash -c "cat > $LOGROTATE_CONF" <<LOGROTATE_EOF
$LOG_FILE {
    daily
    rotate 14
    compress
    missingok
    notifempty
    create 0644 $(whoami) $(whoami)
}
LOGROTATE_EOF
    echo "  ✓ Log rotation configured (14 days, daily)"
else
    echo "  ⚠ logrotate not available. Logs will accumulate at $LOG_FILE"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
echo "  ✅ Setup complete!"
echo "═══════════════════════════════════════════════════"
echo ""
echo "  📅 Tracker will run daily at ${CRON_HOUR}:$(printf '%02d' $CRON_MINUTE) $TIMEZONE"
echo "  📧 Report will be sent to: $(grep RECIPIENT_EMAIL $SCRIPT_DIR/.env | cut -d= -f2)"
echo "  📋 Logs stored at: $LOG_FILE"
echo ""
echo "  To run manually right now:"
echo "    $VENV_DIR/bin/python $SCRIPT_DIR/main.py"
echo ""
echo "  To view logs:"
echo "    tail -f $LOG_FILE"
echo ""
echo "  To edit competitor channels:"
echo "    nano $SCRIPT_DIR/config.py"
echo ""
