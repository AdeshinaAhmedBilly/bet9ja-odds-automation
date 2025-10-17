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
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
        print("Scraping odds from Bet9ja...")
        
        try:
            # Temporary mock data for testing
            # Once you're ready, replace this with actual web scraping
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
            
            print(f"Scraped {len(odds_data)} matches")
            return odds_data
            
        except Exception as e:
            print(f"Error scraping odds: {e}")
            return []
    
    def save_odds(self, odds_data):
        """Save current odds to file"""
        with open(ODDS_FILE, 'w') as f:
            json.dump(odds_data, f, indent=2)
        print(f"Saved odds to {ODDS_FILE}")
    
    def load_previous_odds(self):
        """Load previous odds for comparison"""
        if PREVIOUS_ODDS_FILE.exists():
            with open(PREVIOUS_ODDS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    def compare_odds(self, current_odds, previous_odds):
        """Compare current odds with previous odds"""
        print("Comparing odds...")
        
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
        
        print(f"Found {len(changes)} significant changes")
        return changes


class AlertSystem:
    def __init__(self):
        self.email_sender = os.getenv('EMAIL_SENDER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_receiver = os.getenv('EMAIL_RECEIVER')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def generate_pdf_report(self, current_odds, previous_odds=None, changes=None):
        """Generate a PDF report of odds data"""
        try:
            print("Generating PDF report...")
            
            pdf_path = DATA_DIR / f"odds_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            doc = SimpleDocTemplate(str(pdf_path), pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            title = Paragraph("Bet9ja Odds Report", title_style)
            elements.append(title)
            
            # Timestamp
            timestamp_style = ParagraphStyle(
                'Timestamp',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
            timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", timestamp_style)
            elements.append(timestamp)
            elements.append(Spacer(1, 20))
            
            # Current Odds Table
            subtitle = Paragraph("Current Odds", styles['Heading2'])
            elements.append(subtitle)
            elements.append(Spacer(1, 12))
            
            if current_odds:
                data = [['Match', 'Home', 'Draw', 'Away', 'Updated']]
                for odds in current_odds:
                    data.append([
                        odds['match'],
                        str(odds['home_odds']),
                        str(odds['draw_odds']),
                        str(odds['away_odds']),
                        datetime.fromisoformat(odds['timestamp']).strftime('%H:%M')
                    ])
                
                table = Table(data, colWidths=[3*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
                elements.append(Spacer(1, 20))
            
            # Changes Section
            if changes and len(changes) > 0:
                elements.append(PageBreak())
                changes_title = Paragraph("Significant Odds Changes", styles['Heading2'])
                elements.append(changes_title)
                elements.append(Spacer(1, 12))
                
                for change in changes:
                    match_para = Paragraph(f"<b>{change['match']}</b>", styles['Heading3'])
                    elements.append(match_para)
                    elements.append(Spacer(1, 6))
                    
                    change_data = [['Bet Type', 'Previous', 'Current', 'Change %']]
                    
                    for bet_type in ['home_odds', 'draw_odds', 'away_odds']:
                        odds = change[bet_type]
                        change_pct = odds['change_pct']
                        bet_label = bet_type.replace('_odds', '').replace('_', ' ').title()
                        
                        change_data.append([
                            bet_label,
                            str(odds['previous']),
                            str(odds['current']),
                            f"{change_pct:+.2f}%"
                        ])
                    
                    change_table = Table(change_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
                    change_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(change_table)
                    elements.append(Spacer(1, 15))
            
            # Build PDF
            doc.build(elements)
            print(f"PDF report generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Error generating PDF report: {e}")
            return None
    
    def send_email_alert(self, changes):
        """Send email notification about odds changes"""
        if not all([self.email_sender, self.email_password, self.email_receiver]):
            print("Email credentials not configured - skipping email alert")
            return
        
        try:
            print("Sending email alert...")
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Bet9ja Odds Alert - {len(changes)} Changes Detected'
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            
            # Create email body
            html_body = self._create_email_html(changes)
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.email_sender, self.email_password)
                server.send_message(msg)
            
            print("Email sent successfully")
            
        except Exception as e:
            print(f"Error sending email: {e}")
    
    def send_telegram_alert(self, changes):
        """Send Telegram notification about odds changes"""
        if not all([self.telegram_token, self.telegram_chat_id]):
            print("Telegram credentials not configured - skipping Telegram alert")
            return
        
        try:
            print("Sending Telegram alert...")
            
            message = self._create_telegram_message(changes)
            
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            print("Telegram message sent successfully")
            
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
    
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
            <h2>Bet9ja Odds Changes - {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
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
        message = f"<b>Bet9ja Odds Alert</b>\n"
        message += f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        message += f"Found {len(changes)} significant changes:\n\n"
        
        for change in changes:
            message += f"<b>{change['match']}</b>\n"
            
            for bet_type in ['home_odds', 'draw_odds', 'away_odds']:
                odds = change[bet_type]
                change_pct = odds['change_pct']
                bet_label = bet_type.replace('_odds', '').replace('_', ' ').title()
                
                message += f"  {bet_label}: {odds['previous']} to {odds['current']} "
                message += f"({change_pct:+.2f}%)\n"
            
            message += "\n"
        
        return message


def main():
    """Main execution function"""
    print("=" * 50)
    print("Starting Bet9ja Odds Automation")
    print("=" * 50)
    print()
    
    # Initialize scraper
    scraper = Bet9jaOddsScraper()
    
    # Load previous odds
    previous_odds = scraper.load_previous_odds()
    print(f"Loaded {len(previous_odds)} previous odds records")
    
    # Scrape current odds
    current_odds = scraper.scrape_odds()
    
    if not current_odds:
        print("No odds data scraped. Exiting.")
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
        
        # Generate PDF report with changes
        alert_system = AlertSystem()
        alert_system.generate_pdf_report(current_odds, previous_odds, changes)
        
        if changes:
            print()
            print("=" * 50)
            print("SENDING ALERTS")
            print("=" * 50)
            
            # Send alerts
            alert_system.send_email_alert(changes)
            alert_system.send_telegram_alert(changes)
        else:
            print("No significant odds changes detected")
    else:
        # Generate PDF report even on first run
        alert_system = AlertSystem()
        alert_system.generate_pdf_report(current_odds)
        print("No previous odds data for comparison (first run)")
    
    print()
    print("=" * 50)
    print("Bet9ja Odds Automation Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
