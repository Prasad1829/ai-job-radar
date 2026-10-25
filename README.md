# 🚀 AI Job Radar
**Automatically monitors company career pages and sends Telegram alerts for AI/ML fresher jobs**

---

## What This App Does
- Scans **6 companies** every 3 hours: Infosys, Cognizant, Accenture, IBM, Capgemini, Internshala
- Filters for **AI/ML + Fresher (0–1 yr)** roles only
- Sends instant **Telegram notifications** to your phone
- Runs **free forever** on GitHub Actions (no server needed)

---

## Setup — Step by Step

### Step 1: Create Your Telegram Bot (5 minutes)
1. Open Telegram on your phone
2. Search for **@BotFather** and open it
3. Send: `/newbot`
4. It asks for a name → type: `AI Job Radar`
5. It asks for a username → type: `AIJobRadar_yourname_bot`
6. BotFather sends you a **TOKEN** → copy it (looks like `7123456789:AAFxxxxx`)

### Step 2: Get Your Chat ID
1. Search for **@userinfobot** on Telegram
2. Start it → it shows your **Chat ID** (a number like `987654321`)
3. Copy that number

### Step 3: Put Token in config.py
Open `config.py` and replace:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # paste your token here
CHAT_ID   = "YOUR_CHAT_ID_HERE"     # paste your chat ID here
```

### Step 4: Upload to GitHub
1. Create a free account at **github.com**
2. Create a **New Repository** → name it `ai-job-radar` → make it **Private**
3. Upload all these files to that repository

### Step 5: Add Secrets to GitHub (IMPORTANT — keeps your token safe)
1. In your GitHub repo → click **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add:
   - Name: `BOT_TOKEN`  → Value: your Telegram bot token
   - Name: `CHAT_ID`    → Value: your Telegram chat ID
4. These are hidden from everyone, even you can't read them back

### Step 6: Enable GitHub Actions
1. In your repo → click **Actions** tab
2. Click **"I understand my workflows, go ahead and enable them"**
3. Click on **AI Job Radar - Auto Scan** → click **Run workflow** → **Run workflow**

### Step 7: Test It!
1. Go to **Actions** tab → watch the scan run live
2. Check your Telegram — you should get a message!
3. From now on it runs **automatically every 3 hours** 🎉

---

## Folder Structure
```
job_alert_app/
├── main.py              ← Run this to start a scan
├── config.py            ← Your settings (keywords, companies)
├── database.py          ← Remembers seen jobs (no duplicates)
├── notifier.py          ← Sends Telegram messages
├── requirements.txt     ← Python libraries needed
├── companies/
│   ├── infosys.py       ← Scrapes Infosys careers
│   ├── cognizant.py     ← Scrapes Cognizant careers
│   ├── accenture.py     ← Scrapes Accenture careers
│   ├── ibm.py           ← Scrapes IBM careers
│   ├── capgemini.py     ← Scrapes Capgemini careers
│   └── internshala.py   ← Scrapes Internshala jobs
└── .github/
    └── workflows/
        └── job_alert.yml  ← GitHub Actions auto-scheduler
```

---

## Test on Your Laptop First
```bash
# Install libraries
pip install -r requirements.txt

# Run one scan
python main.py

# Or run with startup welcome message
python main.py --startup
```

---

## Customize It
- **Add more keywords** → edit `JOB_KEYWORDS` in `config.py`
- **Add more companies** → create a new file in `companies/` folder
- **Change check frequency** → edit the `cron` line in `.github/workflows/job_alert.yml`

---

## Troubleshooting
| Problem | Fix |
|---------|-----|
| No Telegram message | Check BOT_TOKEN and CHAT_ID in config.py |
| GitHub Actions fails | Check the Secrets are added correctly |
| No jobs found | Companies may have changed their API — check terminal output |
| Duplicate alerts | Delete `seen_jobs.db` to reset |
