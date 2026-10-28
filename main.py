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

# ─── Naukri scraper ───────────────────────────────────────────────────────────

def scrape_naukri():
    print("🔍 Scanning Naukri.com...")
    jobs = []
    search_urls = [
        "https://www.naukri.com/machine-learning-jobs-in-india?experience=0",
        "https://www.naukri.com/artificial-intelligence-jobs-in-india?experience=0",
        "https://www.naukri.com/data-scientist-jobs-in-india?experience=0",
    ]
    seen_titles = set()

    naukri_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    for page_url in search_urls:
        try:
            r = requests.get(page_url, headers=naukri_headers, timeout=20)
            if r.status_code != 200:
                print(f"  [Naukri] {page_url}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "lxml")

            # Naukri job cards
            cards = (soup.select("article.jobTuple") or
                     soup.select(".cust-job-tuple") or
                     soup.select("[class*='srp-jobtuple']") or
                     soup.select(".job-container"))

            for card in cards[:15]:
                title_el = (card.select_one("a.title") or
                            card.select_one(".title") or
                            card.select_one("h2 a") or
                            card.select_one("a[class*='title']"))
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                comp_el = (card.select_one(".comp-name") or
                           card.select_one(".companyInfo") or
                           card.select_one("[class*='comp']"))
                company = comp_el.get_text(strip=True) if comp_el else "Company"

                loc_el = (card.select_one(".locWdth") or
                          card.select_one(".location") or
                          card.select_one("[class*='loc']"))
                location = loc_el.get_text(strip=True) if loc_el else "India"

                href = title_el.get("href", "")
                job_url = href if href.startswith("http") else f"https://www.naukri.com{href}"

                key = f"{title}{company}"
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                if not is_relevant(f"{title} {company}"):
                    continue

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "experience": "0-1 Years",
                    "url": job_url,
                    "source": "Naukri",
                    "found_at": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            print(f"  [Naukri] Error: {e}")

    print(f"  [Naukri] Found {len(jobs)} relevant jobs")
    return jobs

# ─── Internshala scraper ──────────────────────────────────────────────────────

def scrape_internshala():
    print("🔍 Scanning Internshala...")
    jobs = []
    pages_to_check = [
        "https://internshala.com/jobs/machine-learning-jobs/",
        "https://internshala.com/jobs/artificial-intelligence-jobs/",
        "https://internshala.com/jobs/python-jobs/",
        "https://internshala.com/jobs/data-science-jobs/",
    ]
    seen_titles = set()

    for page_url in pages_to_check:
        try:
            headers = {**HEADERS, "Referer": "https://internshala.com/"}
            r = requests.get(page_url, headers=headers, timeout=15)
            if r.status_code != 200:
                print(f"  [Internshala] {page_url}: HTTP {r.status_code}")
                continue

            soup = BeautifulSoup(r.text, "lxml")

            # Each job card
            cards = soup.select(".individual_internship") or soup.select(".internship-item") or []
            if not cards:
                # Try newer layout
                cards = soup.select("[class*='job']") or []

            for card in cards[:15]:
                # Title
                title_el = (card.select_one(".profile") or
                            card.select_one("h3") or
                            card.select_one(".job-title") or
                            card.select_one("a[class*='title']"))
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                # Company
                comp_el = (card.select_one(".company_name") or
                           card.select_one(".company-name") or
                           card.select_one("p.company"))
                company = comp_el.get_text(strip=True) if comp_el else "Unknown"

                # Location
                loc_el = (card.select_one(".location_link") or
                          card.select_one(".location") or
                          card.select_one("[class*='location']"))
                location = loc_el.get_text(strip=True) if loc_el else "India"

                # URL
                link_el = card.select_one("a[href*='/job-detail/'], a[href*='/jobs/']")
                if link_el:
                    href = link_el.get("href", "")
                    job_url = f"https://internshala.com{href}" if href.startswith("/") else href
                else:
                    job_url = page_url

                key = f"{title}{company}"
                if key in seen_titles:
                    continue
                seen_titles.add(key)

                if not is_relevant(f"{title} {company}"):
                    continue

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "experience": "0-1 Years",
                    "url": job_url,
                    "source": "Internshala",
                    "found_at": datetime.utcnow().isoformat(),
                })

        except Exception as e:
            print(f"  [Internshala] Error for {page_url}: {e}")

    print(f"  [Internshala] Found {len(jobs)} relevant jobs")
    return jobs

# ─── TCS scraper (career page — usually works) ───────────────────────────────

def scrape_tcs():
    print("🔍 Scanning TCS...")
    jobs = []
    try:
        url = "https://ibegin.tcs.com/iBegin/faces/pages/Application/JobPosting/JobSearch.xhtml"
        # TCS uses a different approach — check their public API
        api_url = "https://ibegin.tcs.com/iBegin/api/jobopening/search"
        payload = {
            "searchType": "keyword",
            "keyword": "machine learning",
            "location": "India",
            "experience": "0",
        }
        r = requests.post(api_url, json=payload, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("data", [])[:10]:
                title = j.get("jobTitle", "") or j.get("title", "")
                if not is_relevant(title):
                    continue
                jobs.append({
                    "title": title,
                    "company": "TCS",
                    "location": j.get("location", "India"),
                    "experience": "0-1 Years",
                    "url": f"https://ibegin.tcs.com/iBegin/#{j.get('jobId', '')}",
                    "source": "TCS Careers",
                    "found_at": datetime.utcnow().isoformat(),
                })
    except Exception as e:
        print(f"  [TCS] Error: {e}")

    # Fallback: TCS NQT / NextStep portal
    try:
        r2 = requests.get(
            "https://nextstep.tcs.com/campus/#/jobs",
            headers=HEADERS, timeout=10
        )
    except Exception:
        pass

    print(f"  [TCS] Found {len(jobs)} relevant jobs")
    return jobs

# ─── Wipro scraper ────────────────────────────────────────────────────────────

def scrape_wipro():
    print("🔍 Scanning Wipro...")
    jobs = []
    try:
        url = ("https://careers.wipro.com/careers-home/jobs?stretch=all"
               "&stretchUnit=YEARS&location=India&country=356"
               "&keywords=machine+learning&pagesize=25")
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "lxml")
            cards = soup.select(".article--result, .job-result, [data-ph-at-id]")
            for card in cards[:15]:
                title_el = card.select_one("h2, h3, .title, [class*='title']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not is_relevant(title):
                    continue
                link_el = card.select_one("a")
                href = link_el.get("href", "") if link_el else ""
                job_url = f"https://careers.wipro.com{href}" if href.startswith("/") else href or "https://careers.wipro.com"
                jobs.append({
                    "title": title,
                    "company": "Wipro",
                    "location": "India",
                    "experience": "0-2 Years",
                    "url": job_url,
                    "source": "Wipro Careers",
                    "found_at": datetime.utcnow().isoformat(),
                })
        else:
            print(f"  [Wipro] HTTP {r.status_code}")
    except Exception as e:
        print(f"  [Wipro] Error: {e}")
    print(f"  [Wipro] Found {len(jobs)} relevant jobs")
    return jobs

# ─── Save JSON for dashboard ──────────────────────────────────────────────────

def save_jobs_json(new_jobs):
    existing = []
    if os.path.exists(JOBS_JSON):
        try:
            with open(JOBS_JSON) as f:
                existing = json.load(f)
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
    send_telegram("🤖 AI Job Radar scan started...")
    conn = init_db()

    all_scrapers = [
        scrape_naukri,
        scrape_internshala,
        scrape_wipro,
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
            send_job_alert(job)

    print(f"\n📊 Scan complete: {total_found} found, {total_new} new")
    save_jobs_json(new_jobs)
    send_summary(total_found, total_new)
    conn.close()

if __name__ == "__main__":
    main()
