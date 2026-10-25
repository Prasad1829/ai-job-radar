# ============================================================
#  IBM scraper — uses their public jobs API
#  careers page: https://www.ibm.com/in-en/employment/
# ============================================================

import requests
from config import HEADERS, JOB_KEYWORDS


API_URL = (
    "https://careers.ibm.com/api/jobs/search?"
    "country=India&experience=Entry+Level"
    "&start=0&limit=25&sort=1"
)


def fetch_jobs() -> list:
    jobs = []
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        job_list = data.get("jobs") or data.get("newJobs") or []

        for job in job_list:
            title    = job.get("title", "")
            city     = job.get("primaryCity", "India")
            job_id   = job.get("jobId", "")
            link     = f"https://careers.ibm.com/job/{job_id}"

            if _is_relevant(title):
                jobs.append({
                    "company":   "IBM",
                    "title":     title,
                    "location":  city,
                    "link":      link,
                    "salary":    "",
                    "posted_at": job.get("postedDate", ""),
                })

    except Exception as e:
        print(f"[IBM] Error: {e}")

    print(f"[IBM] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)
