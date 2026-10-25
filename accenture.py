# ============================================================
#  Accenture scraper — uses their public jobs API
#  careers page: https://www.accenture.com/in-en/careers
# ============================================================

import requests
from config import HEADERS, JOB_KEYWORDS


API_URL = (
    "https://www.accenture.com/api/sitecore/Careers/SearchJobs?"
    "countryCode=in&experienceLevel=entry-level"
    "&pageNum=1&pageSize=25"
)


def fetch_jobs() -> list:
    jobs = []
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        job_list = data.get("jobDetails") or data.get("jobs") or []

        for job in job_list:
            title    = job.get("jobTitle", "")
            location = job.get("jobLocation", "India")
            job_id   = job.get("jobId", "")
            link     = f"https://www.accenture.com/in-en/careers/jobdetails?id={job_id}"

            if _is_relevant(title):
                jobs.append({
                    "company":   "Accenture",
                    "title":     title,
                    "location":  location,
                    "link":      link,
                    "salary":    "",
                    "posted_at": job.get("publishedDate", ""),
                })

    except Exception as e:
        print(f"[Accenture] Error: {e}")

    print(f"[Accenture] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)
