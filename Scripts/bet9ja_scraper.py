#!/usr/bin/env python3
"""
Bet9ja Odds Automation Script
Scrapes odds, compares with previous data, and sends alerts
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import pandas as pd

# Configuration
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
ODDS_FILE = DATA_DIR / "odds_history.json"
PREVIOUS_ODDS_FILE = DATA_DIR / "previous_odds.json"

# Thresholds for alerts
ODDS_CHANGE_THRESHOLD = 0.1  # 10% change triggers alert

class Bet9jaOddsScraper:
    def __init__(self):
        self.base_url = "https://www.bet9ja.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_odds(self):
        """
        Scrape current odds from Bet9ja
        NOTE: You'll need to customize this based on the actual Bet9ja structure
        """
        print("🔄 Scraping odds from Bet9ja...")
        
        try:
            # Example structure - customize based on actual Bet9ja pages
            # This is a placeholder that you'll need to adjust
            url = f"{self.base_url}/Sport/Football.aspx"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Placeholder for odds extraction
            # You'll need to inspect Bet9ja's HTML structure and update this
            odds_data = []
            
            # Example structure (customize this):
            # matches = soup.find_all('div', class_='match-item')
            # for match in matches:
            #     odds_data.append({
            #         'match': match.find('span', class_='match-name').text,
            #         'home_odds': float(match.find('span', class_='home-odds').text),
            #         'draw_odds': float(match.find('span', class_='draw-odds').text),
            #         'away_odds': float(match.find('span', class_='away-odds').text),
            #         'timestamp': datetime.now().isoformat()
            #     })
            
            # Temporary mock data for testing
            odds_data = [
                {
                    'match': 'Arsenal vs Chelsea',
                    'home_odds': 2.10,
                    'draw_odds': 3.40,
                    'away_odds': 3.20,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'match': 'Liverpool vs Man United',
                    'home_odds': 1.85,
                    'draw_odds': 3.60,
                    'away_odds': 4.20,
                    'timestamp': datetime.now().isoformat()
                }
            ]
            
            print(f"✅ Scraped {len(odds_data)} matches")
            return odds_data
            
        except Exception as e:
            print(f"❌ Error scraping odds: {e}")
            return []
    
    def save_odds(self, odds_data):
        """Save current odds to file"""
        with open(ODDS_FILE, 'w') as f:
            json.dump(odds_data, f, indent=2)
        print(f"💾 Saved odds to {ODDS_FILE}")
    
    def load_previous_odds(self):
        """Load previous odds for comparison"""
        if PREVIOUS_ODDS_FILE.exists():
            with open(PREVIOUS_ODDS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def compare_odds(self, current_odds, previous_odds):
        """Compare current odds with previous odds"""
        print("🔍 Comparing odds...")
        
        changes = []
        
        # Create lookup dict for previous odds
        prev_dict = {item['match']: item for item in previous_odds}
        
        for current in current_odds:
            match_name = current['match']
            
            if match_name in prev_dict:
                prev = prev_dict[match_name]
                
                # Calculate changes
                home_change = ((current['home_odds'] - prev['home_odds']) / prev['home_odds']) * 100
                draw_change = ((current['draw_odds'] - prev['draw_odds']) / prev['draw_odds']) * 100
                away_change = ((current['away_odds'] - prev['away_odds']) / prev['away_odds']) * 100
                
                # Check if change exceeds threshold
                if (abs(home_change) > ODDS_CHANGE_THRESHOLD * 100 or 
                    abs(draw_change) > ODDS_CHANGE_THRESHOLD * 100 or 
                    abs(away_change) > ODDS_CHANGE_THRESHOLD * 100):
                    
                    changes.append({
                        'match': match_name,
                        'home_odds': {
                            'previous': prev['home_odds'],
                            'current': current['home_odds'],
                            'change_pct': round(home_change, 2)
                        },
                        'draw_odds': {
                            'previous': prev['draw_odds'],
                            'current': current['draw_odds'],
                            'change_pct': round(draw_change, 2)
                        },
                        'away_odds': {
                            'previous': prev['away_odds'],
                            'current': current['away_odds'],
                            'change_pct': round(away_change, 2)
                        }
                    })
        
        print(f"📊 Found {len(changes)} significant changes")
        return changes


class AlertSystem:
    def __init__(self):
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_receiver = os.getenv('EMAIL_RECEIVER')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def send_email_alert(self, changes):
        """Send email notification about odds changes"""
        if not all([self.email_sender, self.email_password, self.email_receiver]):
            print("⚠️ Email credentials not configured")
            return
        
        try:
            print("📧 Sending email alert...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'⚽ Bet9ja Odds Alert - {len(changes)} Changes Detected'
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            
            # Create email body
            html_body = self._create_email_html(changes)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            
            print("✅ Email sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending email: {e}")
    
    def send_telegram_alert(self, changes):
        """Send Telegram notification about odds changes"""
        if not all([self.telegram_token, self.telegram_chat_id]):
            print("⚠️ Telegram credentials not configured")
            return
        
        try:
            print("📱 Sending Telegram alert...")
            
            message = self._create_telegram_message(changes)
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            print("✅ Telegram message sent successfully")
            
        except Exception as e:
            print(f"❌ Error sending Telegram message: {e}")
    
    def _create_email_html(self, changes):
        """Create HTML email body"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #2c3e50; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .increase {{ color: #27ae60; font-weight: bold; }}
                .decrease {{ color: #e74c3c; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h2>⚽ Bet9ja Odds Changes - {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
            <p>The following matches have significant odds changes:</p>
            <table>
                <tr>
                    <th>Match</th>
                    <th>Bet Type</th>
                    <th>Previous</th>
                    <th>Current</th>
                    <th>Change</th>
                </tr>
        """
        
        for change in changes:
            match = change['match']
            
            for bet_type in ['home_odds', 'draw_odds', 'away_odds']:
                odds = change[bet_type]
                change_pct = odds['change_pct']
                change_class = 'increase' if change_pct > 0 else 'decrease'
                bet_label = bet_type.replace('_odds', '').replace('_', ' ').title()
                
                html += f"""
                <tr>
                    <td>{match}</td>
                    <td>{bet_label}</td>
                    <td>{odds['previous']}</td>
                    <td>{odds['current']}</td>
                    <td class="{change_class}">{change_pct:+.2f}%</td>
                </tr>
                """
        
        html += """
            </table>
            <p style="margin-top: 20px; color: #7f8c8d;">
                <em>This is an automated alert from your Bet9ja Odds Automation system.</em>
            </p>
        </body>
        </html>
        """
        
        return html
    
    def _create_telegram_message(self, changes):
        """Create Telegram message"""
        message = f"⚽ <b>Bet9ja Odds Alert</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        message += f"Found {len(changes)} significant changes:\n\n"
        
        for change in changes:
            message += f"🎯 <b>{change['match']}</b>\n"
            
            for bet_type in ['home_odds', 'draw_odds', 'away_odds']:
                odds = change[bet_type]
                change_pct = odds['change_pct']
                emoji = "📈" if change_pct > 0 else "📉"
                bet_label = bet_type.replace('_odds', '').replace('_', ' ').title()
                
                message += f"  {emoji} {bet_label}: {odds['previous']} → {odds['current']} "
                message += f"({change_pct:+.2f}%)\n"
            
            message += "\n"
        
        return message


def main():
    """Main execution function"""
    print("=" * 50)
    print("🚀 Starting Bet9ja Odds Automation")
    print("=" * 50)
    print()
    
    # Initialize scraper
    scraper = Bet9jaOddsScraper()
    
    # Load previous odds
    previous_odds = scraper.load_previous_odds()
    print(f"📂 Loaded {len(previous_odds)} previous odds records")
    
    # Scrape current odds
    current_odds = scraper.scrape_odds()
    
    if not current_odds:
        print("❌ No odds data scraped. Exiting.")
        return
    
    # Save current odds for next comparison
    scraper.save_odds(current_odds)
    
    # Move current to previous for next run
    if ODDS_FILE.exists():
        with open(ODDS_FILE, 'r') as f:
            data = json.load(f)
        with open(PREVIOUS_ODDS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Compare odds if we have previous data
    if previous_odds:
        changes = scraper.compare_odds(current_odds, previous_odds)
        
        if changes:
            print()
            print("=" * 50)
            print("📢 SENDING ALERTS")
            print("=" * 50)
            
            # Send alerts
            alert_system = AlertSystem()
            alert_system.send_email_alert(changes)
            alert_system.send_telegram_alert(changes)
        else:
            print("✅ No significant odds changes detected")
    else:
        print("ℹ️ No previous odds data for comparison (first run)")
    
    print()
    print("=" * 50)
    print("✅ Bet9ja Odds Automation Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
