import os
import json
import hashlib
from datetime import datetime, timezone

from infosys    import fetch_jobs as infosys_jobs
from cognizant  import fetch_jobs as cognizant_jobs
from accenture  import fetch_jobs as accenture_jobs
from ibm        import fetch_jobs as ibm_jobs
from capgemini  import fetch_jobs as capgemini_jobs
from internshala import fetch_jobs as internshala_jobs

from database  import init_db, is_new_job, save_job, log_run, get_recent_jobs
from notifier  import send_job_alert, send_summary, send_error_alert, send_startup_message
from config    import BOT_TOKEN, CHAT_ID

SCRAPERS = {
    "Infosys":     infosys_jobs,
    "Cognizant":   cognizant_jobs,
    "Accenture":   accenture_jobs,
    "IBM":         ibm_jobs,
    "Capgemini":   capgemini_jobs,
    "Internshala": internshala_jobs,
}

def make_job_id(company, title, link=""):
    raw = f"{company}|{title}|{link}"
    return hashlib.md5(raw.encode()).hexdigest()


def save_jobs_json(new_jobs_list):
    """Save job results to jobs_data.json for the dashboard."""
    try:
        jobs_file = 'jobs_data.json'
        existing_jobs = []
        if os.path.exists(jobs_file):
            with open(jobs_file) as f:
                old_data = json.load(f)
                existing_jobs = old_data.get('jobs', [])

        for job in new_jobs_list:
            if 'found_at' not in job:
                job['found_at'] = datetime.now(timezone.utc).isoformat()

        all_jobs = new_jobs_list + existing_jobs
        all_jobs = all_jobs[:200]

        with open(jobs_file, 'w') as f:
            json.dump({
                'last_scan': datetime.now(timezone.utc).isoformat(),
                'jobs': all_jobs
            }, f, indent=2)

        print(f"✅ Saved {len(all_jobs)} total jobs to jobs_data.json ({len(new_jobs_list)} new)")
    except Exception as e:
        print(f"⚠️  Could not save jobs_data.json: {e}")


def run_scan():
    init_db()
    send_startup_message()

    total_found = 0
    total_new   = 0
    new_jobs_list = []
    errors = []

    for company, scraper in SCRAPERS.items():
        print(f"\n🔍 Scanning {company}...")
        try:
            jobs = scraper()
            print(f"   Found {len(jobs)} listings")

            for job in jobs:
                total_found += 1
                job_id = make_job_id(company, job.get('title',''), job.get('link',''))

                if is_new_job(job_id):
                    total_new += 1
                    job['company'] = company
                    save_job(job_id, company, job.get('title',''), job.get('link',''), job.get('location',''))
                    send_job_alert(company, job)
                    new_jobs_list.append(job)
                    print(f"   ✨ NEW: {job.get('title','')}")

        except Exception as e:
            errors.append(f"{company}: {e}")
            print(f"   ❌ Error: {e}")
            send_error_alert(company, str(e))

    print(f"\n📊 Scan complete: {total_found} found, {total_new} new")
    send_summary(total_found, total_new)

    save_jobs_json(new_jobs_list)
    log_run(total_found, total_new)


if __name__ == '__main__':
    run_scan()
