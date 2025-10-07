import pandas as pd
import os
import datetime
import smtplib
from email.mime.text import MIMEText
import requests

# === CONFIGURATION ===
EXCEL_FOLDER = "data"
THRESHOLD_PERCENT_CHANGE = 10  # Alert when % change is above this
EMAIL_SENDER = "youremail@gmail.com"
EMAIL_PASSWORD = "xdxp dgzy xusu kbao"  # App password
EMAIL_RECEIVER = "youremail@gmail.com"

TELEGRAM_BOT_TOKEN = "7430013143:AAHp-qP5TvjvFB8bhS7_Gg3QM6xmye-ghas"
TELEGRAM_CHAT_ID = "5049248116"

# === LOAD YESTERDAY AND TODAY FILES ===
today = datetime.datetime.now().date()
yesterday = today - datetime.timedelta(days=1)
today_file = os.path.join(EXCEL_FOLDER, f"{today}.xlsx")
yesterday_file = os.path.join(EXCEL_FOLDER, f"{yesterday}.xlsx")

if not os.path.exists(today_file) or not os.path.exists(yesterday_file):
    print("Missing one of the files. Make sure both today and yesterday files exist.")
    exit()

df_today = pd.read_excel(today_file)
df_yesterday = pd.read_excel(yesterday_file)

# === COMPARE ODDS ===
merged = pd.merge(
    df_yesterday,
    df_today,
    on=["Match", "Market Type", "Option"],
    suffixes=("_yesterday", "_today")
)

merged["% Change"] = ((merged["Odds_today"] - merged["Odds_yesterday"]) / merged["Odds_yesterday"]) * 100
alerts = merged[merged["% Change"].abs() >= THRESHOLD_PERCENT_CHANGE]

if alerts.empty:
    print("No significant changes found.")
    exit()

# === FORMAT ALERT MESSAGE ===
def format_alert_table(df):
    lines = []
    for _, row in df.iterrows():
        line = f"{row['Match']} | {row['Market Type']} | {row['Option']}\n" +                f"Odds: {row['Odds_yesterday']} → {row['Odds_today']} | Change: {row['% Change']:.2f}%\n"
        lines.append(line)
    return "\n".join(lines)

alert_message = f"⚠️ ODDS CHANGE ALERT ({today}):\n\n" + format_alert_table(alerts)

# === SEND TELEGRAM ALERT ===
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data)
        print("✅ Telegram alert sent.")
    except Exception as e:
        print("❌ Failed to send Telegram message:", e)

# === SEND EMAIL ALERT ===
def send_email(subject, message):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ Email alert sent.")
    except Exception as e:
        print("❌ Failed to send email:", e)

# === RUN ALERTS ===
print("🚨 Significant odds changes detected:")
print(alert_message)

send_telegram(alert_message)
send_email("Odds Alert 🚨", alert_message)