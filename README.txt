Bet9ja Daily Odds Automation System
===================================

This bundle includes the core automation files to scrape, store, compare, and alert on football odds.

FILES:
------
1. daily_scraper.py     - Scrapes odds from your Bet9ja link and saves to Excel, SQLite, and Google Sheets.
2. compare_odds.py      - Compares yesterday's vs today's odds, calculates % difference, and sends alerts.
3. google_credentials.json - Your uploaded Google Sheets credentials.

SETUP:
------
1. Install dependencies:
   pip install -r requirements.txt

2. Run daily scraper (manually or via Task Scheduler/cron):
   python daily_scraper.py

3. Run the comparison:
   python compare_odds.py

4. For dashboard: use odds_dashboard_advanced.py with Streamlit

Telegram and email alerts will notify you when major odds shifts are detected.

Enjoy automated predictions and alerts!