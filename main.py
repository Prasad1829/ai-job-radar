#!/usr/bin/env python3
# ============================================================
#  AI Job Radar — main.py
#  Run this file to start one scan cycle
#  GitHub Actions calls this every 3 hours automatically
# ============================================================

import sys
from database import init_db, is_new_job, save_job, make_job_id, log_run
from notifier import send_job_alert, send_summary, send_error_alert

# Import all company scrapers
from companies.infosys    import fetch_jobs as infosys_jobs
from companies.cognizant  import fetch_jobs as cognizant_jobs
from companies.accenture  import fetch_jobs as accenture_jobs
from companies.ibm        import fetch_jobs as ibm_jobs
from companies.capgemini  import fetch_jobs as capgemini_jobs
from companies.internshala import fetch_jobs as internshala_jobs


SCRAPERS = {
    "Infosys":     infosys_jobs,
    "Cognizant":   cognizant_jobs,
    "Accenture":   accenture_jobs,
    "IBM":         ibm_jobs,
    "Capgemini":   capgemini_jobs,
    "Internshala": internshala_jobs,
}


def run_scan():
    print("\n" + "="*50)
    print("  AI Job Radar — Starting Scan")
    print("="*50 + "\n")

    # Make sure the database exists
    init_db()

    total_found = 0
    total_new   = 0

    for company_name, scraper_fn in SCRAPERS.items():
        print(f"\n--- Scanning {company_name} ---")
        try:
            jobs = scraper_fn()
            total_found += len(jobs)

            for job in jobs:
                job_id = make_job_id(
                    job.get("company", company_name),
                    job.get("title", ""),
                    job.get("link", ""),
                )

                if is_new_job(job_id):
                    print(f"  ✅ NEW: {job['title']} @ {job['company']}")
                    save_job(job)
                    send_job_alert(job)
                    total_new += 1
                else:
                    print(f"  ⏭  Already seen: {job['title']}")

        except Exception as e:
            print(f"  ❌ Error scanning {company_name}: {e}")
            send_error_alert(company_name, str(e))

    # Send summary
    send_summary(total_new, len(SCRAPERS))
    log_run(total_found, total_new)

    print(f"\n{'='*50}")
    print(f"  Scan complete — {total_new} new jobs found out of {total_found} checked")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    # If called with --startup flag, send a welcome message first
    if "--startup" in sys.argv:
        from notifier import send_startup_message
        send_startup_message()

    run_scan()
