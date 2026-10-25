# ============================================================
#  AI Job Radar — notifier.py
#  Sends Telegram alerts when a new job is found
# ============================================================

import requests
from config import BOT_TOKEN, CHAT_ID


TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_job_alert(job: dict):
    """Send one job as a Telegram message."""
    message = _format_message(job)
    _send(message)


def send_summary(total_new: int, companies_checked: int):
    """Send a short summary after each scan (only if new jobs found)."""
    if total_new == 0:
        return  # no message if nothing new — avoid spam

    text = (
        f"✅ *Scan Complete*\n\n"
        f"📊 Checked *{companies_checked}* companies\n"
        f"🆕 Found *{total_new}* new AI/ML job(s)\n\n"
        f"_Check the alerts above to apply!_"
    )
    _send(text)


def send_error_alert(company: str, error: str):
    """Notify if a scraper crashes (optional — won't spam)."""
    text = f"⚠️ *Scraper Error*\n\n🏢 {company}\n❌ {error[:200]}"
    _send(text)


def send_startup_message():
    """Confirm the bot is running when you first set it up."""
    text = (
        "🚀 *AI Job Radar is now running!*\n\n"
        "I'll scan these companies every 3 hours:\n"
        "• Infosys  • Cognizant  • Accenture\n"
        "• IBM  • Capgemini  • Internshala\n\n"
        "Keywords: ML Engineer, AI Engineer, Data Scientist, NLP, GenAI...\n"
        "Experience filter: 0–1 years (Fresher)\n\n"
        "_You'll get a notification the moment a new job is posted!_ 🎯"
    )
    _send(text)


# ----------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------

def _format_message(job: dict) -> str:
    company   = job.get("company", "Unknown")
    title     = job.get("title", "Job Opening")
    location  = job.get("location", "India")
    link      = job.get("link", "")
    salary    = job.get("salary", "")
    posted_at = job.get("posted_at", "")

    lines = [
        f"🚨 *NEW JOB ALERT!*",
        f"",
        f"🏢 *{company}*",
        f"💼 {title}",
        f"📍 {location}",
        f"🎓 0–1 yrs · Fresher",
    ]

    if salary:
        lines.append(f"💰 {salary}")

    if posted_at:
        lines.append(f"📅 Posted: {posted_at}")

    if link:
        lines.append(f"")
        lines.append(f"🔗 [Apply Here]({link})")

    lines.append(f"")
    lines.append(f"_Found by AI Job Radar_")

    return "\n".join(lines)


def _send(text: str):
    """Send a message to your Telegram chat."""
    try:
        payload = {
            "chat_id":    CHAT_ID,
            "text":       text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False,
        }
        resp = requests.post(TELEGRAM_URL, json=payload, timeout=10)
        resp.raise_for_status()
        print(f"[Telegram] Message sent ✓")
    except Exception as e:
        print(f"[Telegram] Failed to send: {e}")
