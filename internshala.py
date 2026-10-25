# ============================================================
#  Internshala scraper — plain HTML scrape (no API needed)
#  page: https://internshala.com/jobs/machine-learning-jobs/
# ============================================================

import requests
from bs4 import BeautifulSoup
from config import HEADERS, JOB_KEYWORDS


PAGES = [
    "https://internshala.com/jobs/machine-learning-jobs/",
    "https://internshala.com/jobs/data-science-jobs/",
    "https://internshala.com/jobs/artificial-intelligence-jobs/",
    "https://internshala.com/jobs/python-jobs/",
]


def fetch_jobs() -> list:
    jobs = []
    seen_links = set()

    for url in PAGES:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Internshala job cards have class "individual_internship"
            cards = soup.find_all("div", class_="individual_internship")

            for card in cards:
                title_tag = card.find("h3", class_="job-internship-name")
                if not title_tag:
                    title_tag = card.find("h3")
                title = title_tag.get_text(strip=True) if title_tag else ""

                company_tag = card.find("h4", class_="company-name")
                company = company_tag.get_text(strip=True) if company_tag else "Company"

                loc_tag = card.find("div", id=lambda x: x and "location_names" in str(x))
                location = loc_tag.get_text(strip=True) if loc_tag else "India"

                link_tag = card.find("a", href=True)
                link = "https://internshala.com" + link_tag["href"] if link_tag else url

                if link in seen_links:
                    continue
                seen_links.add(link)

                if _is_relevant(title):
                    jobs.append({
                        "company":   company,
                        "title":     title,
                        "location":  location,
                        "link":      link,
                        "salary":    "",
                        "posted_at": "",
                    })

        except Exception as e:
            print(f"[Internshala] Error on {url}: {e}")

    print(f"[Internshala] Found {len(jobs)} relevant jobs")
    return jobs


def _is_relevant(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in JOB_KEYWORDS)
