"""
email_reporter.py — Premium Responsive HTML Email Builder & Sender

Advanced, mobile-responsive email template with:
- Branded dark hero header
- Stat summary cards
- Two-column video grid (stacks on mobile)
- Inline CSS for email client compatibility
- Color-coded performance badges
- View to subscriber ratio indicators
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
#  HTML — Full Email Template
# ─────────────────────────────────────────────────────────────────────────────

HTML_WRAPPER = """\
<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>YouTube Competitor Report</title>
  <!--[if mso]>
  <noscript><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml></noscript>
  <![endif]-->
  <style>
    /* Reset */
    *, *:before, *:after {{ box-sizing: border-box; }}
    body, table, td, a {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ -ms-interpolation-mode: bicubic; border: 0; outline: none; text-decoration: none; }}
    body {{ margin: 0; padding: 0; background-color: #0d0d1a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; }}

    /* Responsive grid */
    .video-col {{
      display: inline-block;
      vertical-align: top;
      width: 100%;
      max-width: 280px;
    }}

    /* Mobile */
    @media screen and (max-width: 620px) {{
      .email-container {{ width: 100% !important; }}
      .hero-title {{ font-size: 24px !important; }}
      .hero-sub {{ font-size: 13px !important; }}
      .stat-block {{ display: block !important; width: 100% !important; margin-bottom: 12px !important; }}
      .video-col {{ max-width: 100% !important; display: block !important; margin-bottom: 0 !important; }}
      .card-thumb img {{ width: 100% !important; height: auto !important; }}
      .section-title {{ font-size: 15px !important; }}
      .hide-mobile {{ display: none !important; }}
      .full-mobile {{ width: 100% !important; display: block !important; }}
      .pad-mobile {{ padding: 16px !important; }}
    }}
  </style>
</head>
<body style="margin:0;padding:0;background-color:#0d0d1a;">

<!-- Preheader (hidden preview text) -->
<div style="display:none;font-size:1px;line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">
  {preheader}
</div>

<!-- Email Wrapper -->
<table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#0d0d1a;">
  <tr>
    <td align="center" style="padding:24px 12px;">

      <!-- Email Container -->
      <table role="presentation" class="email-container" cellspacing="0" cellpadding="0" border="0" width="640" style="max-width:640px;width:100%;">

        <!-- ═══ HERO HEADER ════════════════════════════════════════════════ -->
        <tr>
          <td style="border-radius:20px 20px 0 0;background:linear-gradient(135deg,#0d0d1a 0%,#1a1040 40%,#2d1b69 70%,#ff4757 100%);padding:0;overflow:hidden;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td style="padding:40px 36px 32px;text-align:center;">
                  <!-- Icon -->
                  <div style="display:inline-block;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.15);border-radius:16px;padding:12px 18px;margin-bottom:20px;backdrop-filter:blur(10px);">
                    <span style="font-size:28px;">📊</span>&nbsp;
                    <span style="font-size:13px;font-weight:700;color:#fff;letter-spacing:2px;text-transform:uppercase;">Competitor Tracker</span>
                  </div>
                  <!-- Headline -->
                  <h1 class="hero-title" style="margin:0 0 10px;font-size:30px;font-weight:800;color:#ffffff;letter-spacing:-0.5px;line-height:1.2;">
                    {total} Outperforming Video{plural} 🔥
                  </h1>
                  <p class="hero-sub" style="margin:0 0 20px;font-size:14px;color:rgba(255,255,255,0.7);letter-spacing:0.3px;">
                    AI &amp; Automation Niche · Last 24 Hours · {date}
                  </p>
                  <!-- Date pill -->
                  <div style="display:inline-block;background:rgba(255,255,255,0.12);border-radius:30px;padding:6px 18px;">
                    <span style="font-size:12px;color:rgba(255,255,255,0.8);font-weight:500;">🕑 Generated at {time} · Daily Report</span>
                  </div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ STATS BAR ══════════════════════════════════════════════════ -->
        <tr>
          <td style="background:#1a1040;padding:0;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td style="padding:20px 24px;">
                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                    <tr>
                      <td class="stat-block" align="center" style="padding:14px;background:rgba(255,71,87,0.12);border:1px solid rgba(255,71,87,0.25);border-radius:14px;width:30%;">
                        <div style="font-size:26px;font-weight:800;color:#ff4757;">{total}</div>
                        <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Outperforming</div>
                      </td>
                      <td width="12" class="hide-mobile">&nbsp;</td>
                      <td class="stat-block" align="center" style="padding:14px;background:rgba(78,205,196,0.12);border:1px solid rgba(78,205,196,0.25);border-radius:14px;width:30%;">
                        <div style="font-size:26px;font-weight:800;color:#4ecdc4;">{videos_scanned}</div>
                        <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Videos Scanned</div>
                      </td>
                      <td width="12" class="hide-mobile">&nbsp;</td>
                      <td class="stat-block" align="center" style="padding:14px;background:rgba(255,220,0,0.12);border:1px solid rgba(255,220,0,0.25);border-radius:14px;width:30%;">
                        <div style="font-size:26px;font-weight:800;color:#ffd700;">{keywords_count}</div>
                        <div style="font-size:11px;color:rgba(255,255,255,0.5);font-weight:600;text-transform:uppercase;letter-spacing:1px;margin-top:4px;">Keywords Used</div>
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ DIVIDER ════════════════════════════════════════════════════ -->
        <tr>
          <td style="background:#0d0d1a;padding:6px 24px 0;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td style="border-top:1px solid rgba(255,255,255,0.06);font-size:0;line-height:0;">&nbsp;</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ SECTION LABEL ══════════════════════════════════════════════ -->
        <tr>
          <td style="background:#0d0d1a;padding:24px 24px 16px;">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td>
                  <span style="display:inline-block;background:linear-gradient(90deg,#ff4757,#c44569);border-radius:6px;width:4px;height:20px;vertical-align:middle;margin-right:10px;">&nbsp;</span>
                  <span class="section-title" style="font-size:17px;font-weight:700;color:#ffffff;vertical-align:middle;">Today's Outperforming Videos</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- ═══ VIDEO CARDS ════════════════════════════════════════════════ -->
        {video_rows}

        <!-- ═══ EMPTY STATE (shown when no videos) ════════════════════════ -->
        {empty_state}

        <!-- ═══ FOOTER ════════════════════════════════════════════════════ -->
        <tr>
          <td style="background:#0d0d1a;border-radius:0 0 20px 20px;padding:28px 24px;border-top:1px solid rgba(255,255,255,0.06);">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
              <tr>
                <td align="center">
                  <!-- Channel link -->
                  <p style="margin:0 0 10px;font-size:13px;color:rgba(255,255,255,0.4);">
                    Your Channel:&nbsp;
                    <a href="https://www.youtube.com/@thesoloentrepreneur07" style="color:#ff4757;text-decoration:none;font-weight:600;">@thesoloentrepreneur07</a>
                  </p>
                  <!-- Divider -->
                  <div style="border-top:1px solid rgba(255,255,255,0.06);margin:14px 0;"></div>
                  <!-- Meta -->
                  <p style="margin:0;font-size:11px;color:rgba(255,255,255,0.2);line-height:1.6;">
                    Sent by <strong style="color:rgba(255,255,255,0.35);">YouTube Competitor Tracker</strong> · {date}<br>
                    Searches AI keywords in the last 24 hours &amp; flags outperforming videos
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
      <!-- /Email Container -->

    </td>
  </tr>
</table>

</body>
</html>
"""

# ─── Video Card Row (wraps every 2 cards) ─────────────────────────────────────

VIDEO_ROW_OPEN = """\
<tr>
  <td style="background:#0d0d1a;padding:0 16px 16px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
"""

VIDEO_ROW_CLOSE = """\
      </tr>
    </table>
  </td>
</tr>
"""

VIDEO_ROW_SPACER = """\
        <td width="16" class="hide-mobile">&nbsp;</td>
"""

# ─── Individual Video Card ─────────────────────────────────────────────────────

VIDEO_CARD = """\
        <td class="video-col" valign="top" style="width:50%;vertical-align:top;">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                 style="background:#141428;border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,0.07);">
            <!-- Thumbnail -->
            <tr>
              <td style="padding:0;position:relative;">
                <a href="{url}" target="_blank" style="display:block;text-decoration:none;">
                  <img src="{thumbnail}" alt="thumbnail" width="280" height="157"
                       style="width:100%;height:auto;display:block;border-radius:16px 16px 0 0;object-fit:cover;" />
                  <!-- Play overlay label -->
                  <div style="position:absolute;top:10px;right:10px;background:rgba(0,0,0,0.75);border-radius:6px;padding:4px 8px;">
                    <span style="font-size:10px;color:#fff;font-weight:700;letter-spacing:0.5px;">▶ YOUTUBE</span>
                  </div>
                </a>
              </td>
            </tr>

            <!-- Card Body -->
            <tr>
              <td style="padding:16px;">
                <!-- Channel badge -->
                <div style="margin-bottom:8px;">
                  <span style="display:inline-block;background:rgba(255,71,87,0.15);border:1px solid rgba(255,71,87,0.3);
                               border-radius:20px;padding:3px 10px;font-size:10px;font-weight:700;
                               color:#ff6b7a;text-transform:uppercase;letter-spacing:0.5px;">
                    📺 {channel_name}
                  </span>
                </div>
                <!-- Title -->
                <a href="{url}" target="_blank" style="text-decoration:none;">
                  <p style="margin:0 0 12px;font-size:13px;font-weight:700;color:#ffffff;line-height:1.5;
                             display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
                    {title}
                  </p>
                </a>

                <!-- Stats Row -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                       style="margin-bottom:12px;">
                  <tr>
                    <td style="width:50%;padding:8px;background:rgba(78,205,196,0.08);border-radius:8px;text-align:center;">
                      <div style="font-size:16px;font-weight:800;color:#4ecdc4;">{views}</div>
                      <div style="font-size:9px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;font-weight:600;">Views</div>
                    </td>
                    <td width="8">&nbsp;</td>
                    <td style="width:50%;padding:8px;background:rgba(255,220,0,0.08);border-radius:8px;text-align:center;">
                      <div style="font-size:16px;font-weight:800;color:#ffd700;">{engagement_rate}%</div>
                      <div style="font-size:9px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:1px;font-weight:600;">Engagement</div>
                    </td>
                  </tr>
                </table>

                <!-- Likes & Comments -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                       style="margin-bottom:12px;">
                  <tr>
                    <td style="font-size:11px;color:rgba(255,255,255,0.45);">
                      👍&nbsp;<strong style="color:rgba(255,255,255,0.7);">{likes}</strong>&nbsp;&nbsp;
                      💬&nbsp;<strong style="color:rgba(255,255,255,0.7);">{comments}</strong>&nbsp;&nbsp;
                      📅&nbsp;<span style="color:rgba(255,255,255,0.5);">{published_at}</span>
                    </td>
                  </tr>
                </table>

                <!-- Reason Badges -->
                <div>
                  {reason_badges}
                </div>

                <!-- CTA Button -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%"
                       style="margin-top:14px;">
                  <tr>
                    <td align="center"
                        style="background:linear-gradient(135deg,#ff4757,#c44569);border-radius:8px;">
                      <a href="{url}" target="_blank"
                         style="display:block;padding:9px 14px;font-size:12px;font-weight:700;
                                color:#ffffff;text-decoration:none;letter-spacing:0.3px;">
                        ▶&nbsp; Watch Video
                      </a>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
"""

REASON_BADGE = """\
<span style="display:inline-block;background:{bg};border:1px solid {border};
             border-radius:6px;padding:3px 8px;font-size:10px;font-weight:700;
             color:{color};margin:2px 2px 2px 0;">{text}</span>
"""

EMPTY_STATE_HTML = """\
<tr>
  <td style="background:#0d0d1a;padding:20px 24px 24px;">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
      <tr>
        <td align="center"
            style="background:#141428;border-radius:16px;padding:48px 24px;border:1px dashed rgba(255,255,255,0.1);">
          <p style="font-size:48px;margin:0 0 12px;">✅</p>
          <p style="font-size:17px;font-weight:700;color:#ffffff;margin:0 0 8px;">No Outperforming Videos Today</p>
          <p style="font-size:13px;color:rgba(255,255,255,0.4);margin:0;line-height:1.6;">
            Your tracker ran successfully and scanned all AI keywords.<br>No videos met the performance thresholds in the last 24 hours.
          </p>
        </td>
      </tr>
    </table>
  </td>
</tr>
"""


# ─── Badge Style Helper ────────────────────────────────────────────────────────

def _badge(reason: str) -> str:
    r = reason.lower()
    if "🚀" in reason or "views in 24h" in r or "> 20" in r:
        bg, border, color = "rgba(255,71,87,0.15)", "rgba(255,71,87,0.4)", "#ff6b7a"
    elif "engagement" in r or "💬" in reason:
        bg, border, color = "rgba(78,205,196,0.15)", "rgba(78,205,196,0.4)", "#4ecdc4"
    else:
        bg, border, color = "rgba(255,220,0,0.15)", "rgba(255,220,0,0.4)", "#ffd700"
    return REASON_BADGE.format(bg=bg, border=border, color=color, text=reason)


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


# ─── Build HTML ───────────────────────────────────────────────────────────────

def build_html_email(
    outperforming_videos: list[dict],
    videos_scanned: int = 0,
    keywords_count: int = 0,
) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    now   = datetime.now().strftime("%I:%M %p")
    total = len(outperforming_videos)

    # ── Video rows (2-column grid) ────────────────────────────────────────────
    video_rows_html = ""
    empty_html      = ""

    if not outperforming_videos:
        empty_html = EMPTY_STATE_HTML
    else:
        # Pair videos into rows of 2
        for i in range(0, len(outperforming_videos), 2):
            pair = outperforming_videos[i:i+2]
            video_rows_html += VIDEO_ROW_OPEN

            for j, v in enumerate(pair):
                if j > 0:
                    video_rows_html += VIDEO_ROW_SPACER

                badges_html = "".join(_badge(r) for r in v["reasons"])
                thumb = v.get("thumbnail", "")
                if not thumb:
                    thumb = "https://via.placeholder.com/280x157/141428/4ecdc4?text=No+Thumbnail"

                video_rows_html += VIDEO_CARD.format(
                    url=v["url"],
                    thumbnail=thumb,
                    channel_name=v["channel_name"][:22],
                    title=v["title"].replace("<", "&lt;").replace(">", "&gt;"),
                    views=_fmt(v["views"]),
                    engagement_rate=v["engagement_rate"],
                    likes=_fmt(v["likes"]),
                    comments=_fmt(v["comments"]),
                    published_at=v.get("published_at", ""),
                    reason_badges=badges_html,
                )

            # If only 1 video in the pair, add an empty cell for layout
            if len(pair) == 1:
                video_rows_html += VIDEO_ROW_SPACER
                video_rows_html += """\
        <td class="video-col" valign="top" style="width:50%;vertical-align:top;">
          &nbsp;
        </td>
"""

            video_rows_html += VIDEO_ROW_CLOSE

    preheader = (
        f"🔥 {total} outperforming AI videos found in the last 24 hours!"
        if total > 0 else
        "✅ Tracker ran successfully — no outperforming videos today."
    )

    return HTML_WRAPPER.format(
        preheader=preheader,
        total=total,
        plural="s" if total != 1 else "",
        date=today,
        time=now,
        videos_scanned=_fmt(videos_scanned) if videos_scanned else "—",
        keywords_count=keywords_count if keywords_count else "—",
        video_rows=video_rows_html,
        empty_state=empty_html,
    )


# ─── Plain Text Fallback ──────────────────────────────────────────────────────

def build_plain_text_email(outperforming_videos: list[dict]) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    total = len(outperforming_videos)
    lines = [
        f"YouTube Competitor Tracker — {today}",
        "=" * 52,
        f"Found {total} outperforming video(s) in the last 24 hours.\n",
    ]
    if not outperforming_videos:
        lines.append("No outperforming videos found today. Tracker ran successfully.")
    else:
        for i, v in enumerate(outperforming_videos, 1):
            lines += [
                f"\n{'─' * 40}",
                f"#{i}  {v['title']}",
                f"     Channel:    {v['channel_name']}",
                f"     Views:      {v['views']:,}",
                f"     Likes:      {v['likes']:,}",
                f"     Comments:   {v['comments']:,}",
                f"     Engagement: {v['engagement_rate']}%",
                f"     Published:  {v.get('published_at', '')}",
                f"     URL:        {v['url']}",
                f"     Why:        {' | '.join(v['reasons'])}",
            ]
    lines += ["", "─" * 52,
              "Sent by YouTube Competitor Tracker",
              "Channel: https://www.youtube.com/@thesoloentrepreneur07"]
    return "\n".join(lines)


# ─── Sender ───────────────────────────────────────────────────────────────────

class EmailReporter:
    def __init__(self):
        self.smtp_host     = os.environ["SMTP_HOST"]
        self.smtp_port     = int(os.environ["SMTP_PORT"])
        self.smtp_user     = os.environ["SMTP_USER"]
        self.smtp_password = os.environ["SMTP_PASSWORD"]
        self.recipient     = os.environ["RECIPIENT_EMAIL"]

    def send_report(
        self,
        outperforming_videos: list[dict],
        videos_scanned: int = 0,
        keywords_count: int = 0,
    ) -> bool:
        today = datetime.now().strftime("%B %d, %Y")
        total = len(outperforming_videos)

        subject = (
            f"🔥 {total} Outperforming AI Video{'s' if total != 1 else ''} Today — {today}"
            if total > 0 else
            f"✅ Competitor Tracker — No outperformers today · {today}"
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = f"YouTube Tracker 📊 <{self.smtp_user}>"
        msg["To"]      = self.recipient

        plain = build_plain_text_email(outperforming_videos)
        html  = build_html_email(outperforming_videos, videos_scanned, keywords_count)

        msg.attach(MIMEText(plain, "plain", "utf-8"))
        msg.attach(MIMEText(html,  "html",  "utf-8"))

        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, self.recipient, msg.as_string())
            logger.info(f"Email sent to {self.recipient} — {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
