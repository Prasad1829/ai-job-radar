# ============================================================
#  Infosys scraper — uses their internal jobs API
#  careers page: https://career.infosys.com/joblist
# ============================================================

import requests
from config import HEADERS, JOB_KEYWORDS, MAX_EXPERIENCE_YEARS


API_URL = (
    "https://career.infosys.com/api/jobs?"
    "category=fresher&country=India&page=1&limit=50"
)


def fetch_jobs() -> list:
    jobs = []
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        # Infosys API returns {"jobList": [...]}
        job_list = data.get("jobList") or data.get("jobs") or []

        for job in job_list:
            title    = job.get("jobTitle", "")
            location = job.get("jobLocation", "India")
            link     = f"https://career.infosys.com/jobdesc?jobReferenceCode={job.get('jobReferenceCode','')}"
            exp      = job.get("experience", "0-1")

            if _is_relevant(title) and _is_fresher(exp):
                jobs.append({
                    "company":   "Infosys",
                    "title":     title,
                    "location":  location,
                    "link":      link,
                    "salary":    job.get("ctc", ""),
                    "posted_at": job.get("postingDate", ""),
                })

    except Exception as e:
        print(f"[Infosys] Error: {e}")

    print(f"[Infosys] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)


def _is_fresher(exp_str: str) -> bool:
    """Return True if experience requirement is 0 or 1 year."""
    try:
        # exp_str may be "0-1", "0", "1", "fresher" etc.
        if "fresher" in str(exp_str).lower():
            return True
        nums = [int(x) for x in str(exp_str).split("-") if x.strip().isdigit()]
        if nums:
            return min(nums) <= MAX_EXPERIENCE_YEARS
    except Exception:
        pass
    return True  # if we can't parse, include it
