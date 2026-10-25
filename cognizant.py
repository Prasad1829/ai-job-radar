# ============================================================
#  Cognizant scraper — uses their jobs search API
#  careers page: https://careers.cognizant.com
# ============================================================

import requests
from config import HEADERS, JOB_KEYWORDS, MAX_EXPERIENCE_YEARS


API_URL = (
    "https://careers.cognizant.com/api/apply/v2/jobs?"
    "domain=cognizant.com&start=0&num=25"
    "&location=India&experience=0-1+Years"
    "&src=JB_INDEED"
)


def fetch_jobs() -> list:
    jobs = []
    try:
        headers = {**HEADERS, "Accept": "application/json"}
        resp = requests.get(API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        positions = data.get("positions") or []

        for pos in positions:
            title    = pos.get("title", "")
            location = pos.get("location", "India")
            link     = pos.get("canonicalPositionUrl", "https://careers.cognizant.com")
            exp      = pos.get("experienceLevel", "")

            if _is_relevant(title):
                jobs.append({
                    "company":   "Cognizant",
                    "title":     title,
                    "location":  location,
                    "link":      link,
                    "salary":    "",
                    "posted_at": pos.get("postedDate", ""),
                })

    except Exception as e:
        print(f"[Cognizant] Error: {e}")

    print(f"[Cognizant] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)
