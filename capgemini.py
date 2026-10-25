# ============================================================
#  Capgemini scraper — uses their jobs search API
#  careers page: https://www.capgemini.com/in-en/careers/
# ============================================================

import requests
from config import HEADERS, JOB_KEYWORDS


API_URL = (
    "https://www.capgemini.com/in-en/wp-json/cap/v1/jobs?"
    "country=India&experience=fresher&page=1&per_page=25"
)

FALLBACK_URL = (
    "https://www.capgemini.com/in-en/careers/job-search/"
    "?filter_jobtypegroup=students_graduates"
)


def fetch_jobs() -> list:
    jobs = []
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        job_list = data if isinstance(data, list) else data.get("jobs", [])

        for job in job_list:
            title    = job.get("title", {})
            if isinstance(title, dict):
                title = title.get("rendered", "")
            location = job.get("location", "India")
            link     = job.get("link", FALLBACK_URL)

            if _is_relevant(str(title)):
                jobs.append({
                    "company":   "Capgemini",
                    "title":     str(title),
                    "location":  location,
                    "link":      link,
                    "salary":    "",
                    "posted_at": job.get("date", ""),
                })

    except Exception as e:
        print(f"[Capgemini] Error: {e}")

    print(f"[Capgemini] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)
