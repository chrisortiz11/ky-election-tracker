# 🗳️ KY 2026 Democratic Senate Primary Tracker

Live results tracker for the **May 19, 2026** Kentucky Democratic US Senate primary.

**Amy McGrath (AM) vs Charles Booker (CB)**

Data source: [Kentucky Secretary of State live results](https://vrsws.sos.ky.gov/liveresults/)

---

## Quick Start (Local)

```bash
# 1. Clone / copy these files into a folder
# 2. Install dependencies
pip install -r requirements.txt

# 3. Run
streamlit run app.py
```

Your browser will open automatically at `http://localhost:8501`

---

## Deploy to Streamlit Cloud (free, shareable link)

1. Push this folder to a **public GitHub repo**
2. Go to [streamlit.io](https://streamlit.io) → Sign in with GitHub
3. Click **New app** → select your repo → `app.py` as the main file
4. Click **Deploy** — done. Share the URL with your group

---

## What It Shows

| Section | Description |
|---|---|
| **Currently Reporting** | Statewide totals — all reporting counties |
| **100% In Only** | Results only from fully-reported counties |
| **Outstanding** | Partial counties still coming in |
| **DEMOS** | AM vs CB by county type (white, Black, rural, urban, suburban, college) |
| **County Table** | Row-by-row county results (% share + raw votes) |

Auto-refreshes every **90 seconds**. Hit "🔄 Refresh Now" to force a fresh pull.

---

## Notes

- Data is scraped directly from the KY SoS site — no API key needed
- All 120 counties are fetched in parallel (~5–8 seconds per refresh)
- Demographic thresholds match your girlfriend's historical tracker
- Votes are **unofficial** until certified
