# ============================================================
#  AI Job Radar — config.py
#  Edit this file to customize your job alerts
# ============================================================

# ----------------------------------------------------------
# TELEGRAM SETTINGS
# How to get these:
#   1. Open Telegram → search @BotFather → send /newbot
#   2. Copy the token it gives you → paste below as BOT_TOKEN
#   3. Open @userinfobot → it shows your chat ID → paste below
# ----------------------------------------------------------
BOT_TOKEN = "8790053401:AAHdU1mI_XQrWBoOAJuaf2TqremvPNtukCk"       # e.g. "7123456789:AAFxxxxxxxxxxxxx"
CHAT_ID   = "5718663811"         # e.g. "987654321"



# ----------------------------------------------------------
# JOB KEYWORDS  (app alerts only when title matches these)
# ----------------------------------------------------------
JOB_KEYWORDS = [
    "machine learning",
    "ml engineer",
    "ai engineer",
    "data scientist",
    "deep learning",
    "nlp engineer",
    "artificial intelligence",
    "computer vision",
    "mlops",
    "data analyst",
    "python developer",
    "generative ai",
    "genai",
    "llm",
]

# ----------------------------------------------------------
# EXPERIENCE FILTER  (skip jobs needing more experience)
# ----------------------------------------------------------
MAX_EXPERIENCE_YEARS = 1   # only 0-1 year experience roles

# ----------------------------------------------------------
# COMPANIES TO WATCH  (name → careers page URL)
# ----------------------------------------------------------
COMPANIES = {
    "Infosys": {
        "url": "https://career.infosys.com/joblist",
        "type": "api",   # uses internal API — see companies/infosys.py
    },
    "Cognizant": {
        "url": "https://careers.cognizant.com/global/en/search-results",
        "type": "playwright",
    },
    "Accenture": {
        "url": "https://www.accenture.com/in-en/careers/jobsearch?jk=&sb=1&vw=0&is_rj=0&ct=India&pg=1",
        "type": "playwright",
    },
    "IBM": {
        "url": "https://www.ibm.com/in-en/employment/",
        "type": "api",   # IBM has a public jobs API
    },
    "Capgemini": {
        "url": "https://www.capgemini.com/in-en/careers/job-search/?filter_jobtypegroup=students_graduates",
        "type": "playwright",
    },
    "Internshala": {
        "url": "https://internshala.com/jobs/machine-learning-jobs/",
        "type": "requests",  # plain HTML page — easiest to scrape
    },
}

# ----------------------------------------------------------
# CHECK INTERVAL  (how often GitHub Actions runs this)
# Change here AND in .github/workflows/job_alert.yml
# ----------------------------------------------------------
CHECK_EVERY_HOURS = 3

# ----------------------------------------------------------
# DATABASE FILE PATH
# ----------------------------------------------------------
DB_PATH = "seen_jobs.db"

# ----------------------------------------------------------
# REQUEST HEADERS  (looks like a real browser to avoid blocks)
# ----------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
