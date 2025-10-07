import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import os
import sqlite3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === CONFIGURATION ===
BET9JA_URL = "https://web.bet9ja.com/Sport/OddsPrint.ashx?..."  # Replace with your real Bet9ja odds URL
SNAPSHOT_TYPE = "Initial"  # or "Current", "Live", etc.

# === GOOGLE SHEETS SETUP ===
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = "google_credentials.json"
SHEET_NAME = "Bet9ja Odds Tracker"

# === FILE PATHS ===
today = datetime.datetime.now().strftime('%Y-%m-%d')
timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
excel_dir = "data"
excel_path = os.path.join(excel_dir, f"{today}.xlsx")
db_path = "odds.db"

# === SCRAPE DATA ===
print("Scraping Bet9ja odds...")
response = requests.get(BET9JA_URL)
soup = BeautifulSoup(response.content, 'lxml')

records = []
event_blocks = soup.find_all("div", class_="evento")

for event in event_blocks:
    header = event.find("div", class_="evento-head")
    if not header:
        continue

    match_info = header.get_text(separator="|").strip().split("|")
    match_name = match_info[0] if len(match_info) > 0 else "Unknown Match"
    match_time = match_info[1] if len(match_info) > 1 else "Unknown Time"

    market_sections = event.find_all("div", class_="blocco-mercati")
    for market in market_sections:
        market_name_el = market.find("div", class_="intestazione")
        market_name = market_name_el.get_text(strip=True) if market_name_el else "Unknown Market"

        options = market.find_all("div", class_="opzione")
        for option in options:
            outcome = option.find("div", class_="nome")
            odd = option.find("div", class_="quota")
            if outcome and odd:
                records.append({
                    "Date": today,
                    "Time": match_time,
                    "Match": match_name,
                    "Market Type": market_name,
                    "Option": outcome.text.strip(),
                    "Odds": float(odd.text.strip()),
                    "Snapshot Type": SNAPSHOT_TYPE,
                    "Timestamp": timestamp
                })

df = pd.DataFrame(records)
if df.empty:
    print("No odds found. Exiting.")
    exit()

# === SAVE TO EXCEL ===
os.makedirs(excel_dir, exist_ok=True)
df.to_excel(excel_path, index=False)
print(f"✅ Saved to Excel: {excel_path}")

# === SAVE TO SQLITE ===
conn = sqlite3.connect(db_path)
df.to_sql("odds", conn, if_exists="append", index=False)
conn.close()
print(f"✅ Saved to SQLite: {db_path}")

# === SAVE TO GOOGLE SHEETS ===
print("Uploading to Google Sheets...")
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
client = gspread.authorize(creds)

try:
    sheet = client.open(SHEET_NAME)
except:
    sheet = client.create(SHEET_NAME)

try:
    ws = sheet.worksheet(today)
except:
    ws = sheet.add_worksheet(title=today, rows="1000", cols="10")

ws.clear()
ws.update([df.columns.values.tolist()] + df.values.tolist())
print("✅ Saved to Google Sheets tab:", today)