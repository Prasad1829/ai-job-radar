import os
import json
import sqlite3
import hashlib
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
DB_PATH = "seen_jobs.db"
JOBS_JSON = "jobs_data.json"

KEYWORDS = ["machine learning", "ml engineer", "ai engineer", "data scientist",
            "deep learning", "nlp", "computer vision", "artificial intelligence",
            "python developer", "data engineer"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.google.com/",
}

# ─── DB setup ────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    # Fix schema mismatch: if old table has wrong columns, recreate it
    try:
        conn.execute("INSERT OR IGNORE INTO seen_jobs VALUES (?,?)", ("__test__", "__test__"))
        conn.execute("DELETE FROM seen_jobs WHERE id='__test__'")
        conn.commit()
    except sqlite3.OperationalError:
        print("[DB] Schema mismatch detected — recreating seen_jobs table")
        conn.execute("DROP TABLE IF EXISTS seen_jobs")
        conn.execute("""CREATE TABLE seen_jobs (
            id TEXT PRIMARY KEY, seen_at TEXT
        )""")
        conn.commit()
    # Ensure table exists for fresh runs
    conn.execute("""CREATE TABLE IF NOT EXISTS seen_jobs (
        id TEXT PRIMARY KEY, seen_at TEXT
    )""")
    conn.commit()
    return conn

def is_new(conn, job_id):
    cur = conn.execute("SELECT 1 FROM seen_jobs WHERE id=?", (job_id,))
    return cur.fetchone() is None

def mark_seen(conn, job_id):
    conn.execute("INSERT OR IGNORE INTO seen_jobs VALUES (?,?)",
                 (job_id, datetime.utcnow().isoformat()))
    conn.commit()

def job_id(title, company, url=""):
    return hashlib.md5(f"{title}{company}{url}".lower().encode()).hexdigest()[:12]

# ─── Keyword check ────────────────────────────────────────────────────────────

def is_relevant(text):
    t = text.lower()
    return any(kw in t for kw in KEYWORDS)

# ─── Indeed RSS scraper ───────────────────────────────────────────────────────
# Indeed RSS works from GitHub Actions — no blocking, aggregates all Indian job sites

def scrape_indeed_rss():
    print("🔍 Scanning Indeed (RSS)...")
    jobs = []
    seen_titles = set()

    searches = [
        "machine+learning+fresher",
        "artificial+intelligence+fresher",
        "data+scientist+fresher",
        "python+developer+fresher+ai",
        "ml+engineer+fresher",
    ]

    rss_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; RSS reader)",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }

    for query in searches:
        try:
            url = (
                f"https://in.indeed.com/rss"
                f"?q={query}&l=India&sort=date&fromage=7"
            )
            r = requests.get(url, headers=rss_headers, timeout=15)
            if r.status_code != 200:
                print(f"  [Indeed] {query}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "xml")
            items = soup.find_all("item")

            for item in items[:20]:
                title = item.find("title")
                title = title.get_text(strip=True) if title else ""

                link = item.find("link")
                job_url = link.get_text(strip=True) if link else "https://in.indeed.com"

                # Company from source or description
                source_tag = item.find("source")
                company = source_tag.get_text(strip=True) if source_tag else ""

                desc = item.find("description")
                desc_text = desc.get_text(strip=True) if desc else ""

                # Extract company/location from description
                location = "India"
                if "location:" in desc_text.lower():
                    loc_start = desc_text.lower().find("location:")
                    loc_part = desc_text[loc_start+9:loc_start+50].split("<")[0].strip()
                    if loc_part:
                        location = loc_part

                key = f"{title}{company}"
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                if not is_relevant(f"{title} {desc_text[:200]}"):
                    continue

                jobs.append({
                    "title": title,
                    "company": company or "Via Indeed",
                    "location": location,
                    "experience": "0-1 Years",
                    "url": job_url,
                    "source": "Indeed India",
                    "found_at": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            print(f"  [Indeed] Error for '{query}': {e}")

    print(f"  [Indeed] Found {len(jobs)} relevant jobs")
    return jobs


# ─── LinkedIn RSS scraper ─────────────────────────────────────────────────────

def scrape_linkedin_rss():
    print("🔍 Scanning LinkedIn Jobs...")
    jobs = []
    seen_titles = set()

    # LinkedIn public job search URLs (no login needed for listing)
    searches = [
        ("machine learning", "India"),
        ("artificial intelligence fresher", "India"),
        ("data scientist entry level", "India"),
    ]

    for keyword, location in searches:
        try:
            url = (
                "https://www.linkedin.com/jobs/search/?"
                f"keywords={requests.utils.quote(keyword)}"
                f"&location={requests.utils.quote(location)}"
                f"&f_E=1&f_E=2&sortBy=DD&f_TPR=r86400"
            )
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  [LinkedIn] HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "lxml")
            cards = (soup.select("div.base-card") or
                     soup.select(".job-search-card") or
                     soup.select("[class*='base-card']"))

            for card in cards[:10]:
                title_el = card.select_one("h3.base-search-card__title, h3, .job-title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                comp_el = card.select_one("h4.base-search-card__subtitle, h4, .company-name")
                company = comp_el.get_text(strip=True) if comp_el else "Company"

                loc_el = card.select_one(".job-search-card__location, .location")
                loc = loc_el.get_text(strip=True) if loc_el else "India"

                link_el = card.select_one("a.base-card__full-link, a")
                job_url = link_el.get("href", "https://linkedin.com/jobs") if link_el else "https://linkedin.com/jobs"

                key = f"{title}{company}"
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                if not is_relevant(f"{title} {company}"):
                    continue

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "experience": "0-2 Years",
                    "url": job_url,
                    "source": "LinkedIn",
                    "found_at": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            print(f"  [LinkedIn] Error: {e}")

    print(f"  [LinkedIn] Found {len(jobs)} relevant jobs")
    return jobs

# ─── Save JSON for dashboard ──────────────────────────────────────────────────

def save_jobs_json(new_jobs):
    existing = []
    if os.path.exists(JOBS_JSON):
        try:
            with open(JOBS_JSON) as f:
                data = json.load(f)
                # Ensure it's a list of dicts (not corrupt/old format)
                existing = [j for j in data if isinstance(j, dict)]
        except Exception:
            existing = []

    # Add unique new jobs at top
    existing_ids = {job_id(j["title"], j["company"], j.get("url","")) for j in existing}
    added = 0
    for j in new_jobs:
        jid = job_id(j["title"], j["company"], j.get("url",""))
        if jid not in existing_ids:
            existing.insert(0, j)
            existing_ids.add(jid)
            added += 1

    # Keep last 200
    existing = existing[:200]

    with open(JOBS_JSON, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"✅ Saved {len(existing)} total jobs to {JOBS_JSON} ({added} new)")
    return added

# ─── Telegram ────────────────────────────────────────────────────────────────

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("[Telegram] BOT_TOKEN or CHAT_ID not set")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }, timeout=10)
        if r.status_code == 200:
            print("[Telegram] Message sent ✓")
        else:
            print(f"[Telegram] Error {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"[Telegram] Exception: {e}")

def send_job_alert(job):
    msg = (
        f"🚀 <b>New AI/ML Job!</b>\n\n"
        f"📌 <b>{job['title']}</b>\n"
        f"🏢 {job['company']}\n"
        f"📍 {job.get('location','India')}\n"
        f"⏳ {job.get('experience','Fresher')}\n"
        f"🔗 <a href='{job['url']}'>Apply Now</a>\n"
        f"📡 Source: {job.get('source','')}"
    )
    send_telegram(msg)

def send_summary(total_found, total_new):
    now = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    if total_new == 0:
        msg = f"🔍 Scan done ({now})\nNo new AI/ML jobs found this round. Will check again in 3 hours."
    else:
        msg = (
            f"✅ Scan done ({now})\n"
            f"Found {total_found} jobs total, {total_new} NEW alerts sent!"
        )
    send_telegram(msg)

# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    # Debug: print whether secrets are loaded (never print actual values)
    print(f"[Config] BOT_TOKEN set: {bool(BOT_TOKEN)}, CHAT_ID set: {bool(CHAT_ID)}")

    send_telegram("🤖 AI Job Radar scan started...")
    conn = init_db()

    all_scrapers = [
        scrape_indeed_rss,
        scrape_linkedin_rss,
    ]

    all_jobs = []
    for scraper in all_scrapers:
        try:
            jobs = scraper()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Scraper error: {e}")

    total_found = len(all_jobs)
    total_new = 0
    new_jobs = []

    for job in all_jobs:
        jid = job_id(job["title"], job["company"], job.get("url", ""))
        if is_new(conn, jid):
            mark_seen(conn, jid)
            total_new += 1
            new_jobs.append(job)

    print(f"\n📊 Scan complete: {total_found} found, {total_new} new")
    save_jobs_json(new_jobs)

    # Send grouped alert for new jobs (max 10 per message to avoid Telegram limits)
    if new_jobs:
        lines = [f"🚀 <b>{total_new} New AI/ML Jobs Found!</b>\n"]
        for j in new_jobs[:10]:
            lines.append(
                f"📌 <b>{j['title']}</b>\n"
                f"   🏢 {j['company']} | 📍 {j.get('location','India')}\n"
                f"   🔗 <a href='{j['url']}'>Apply</a> | 📡 {j.get('source','')}\n"
            )
        if len(new_jobs) > 10:
            lines.append(f"\n...and {len(new_jobs)-10} more. Check the dashboard!")
        send_telegram("\n".join(lines))

    send_summary(total_found, total_new)
    conn.close()

if __name__ == "__main__":
    main()
