#!/usr/bin/env python3
"""
Bet9ja.com Odds Scraper
Automatically collects football odds data from bet9ja.com
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from datetime import datetime, timedelta
import logging
from urllib.parse import urljoin, urlparse
import csv
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bet9ja_scraper.log'),
        logging.StreamHandler()
    ]
)

class Bet9jaScraper:
    def __init__(self):
        self.base_url = "https://www.bet9ja.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.matches_data = []
        
    def get_page_content(self, url, max_retries=3):
        """Fetch page content with retry logic"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                return response.content
            except requests.RequestException as e:
                logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    logging.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
                time.sleep(2)
        return None

    def parse_match_odds(self, match_element):
        """Extract odds data from a match element"""
        try:
            # Extract team names
            teams = match_element.find_all('span', class_='team-name') or \
                   match_element.find_all('div', class_='team-name') or \
                   match_element.find_all(string=True)
            
            if len(teams) >= 2:
                home_team = teams[0].strip() if hasattr(teams[0], 'strip') else str(teams[0]).strip()
                away_team = teams[1].strip() if hasattr(teams[1], 'strip') else str(teams[1]).strip()
            else:
                return None
            
            # Extract odds (1X2 - Home, Draw, Away)
            odds_elements = match_element.find_all('span', class_='odd-value') or \
                           match_element.find_all('div', class_='odds') or \
                           match_element.find_all(text=lambda text: text and text.replace('.', '').isdigit())
            
            odds = []
            for odd in odds_elements[:3]:  # Take first 3 odds (Home, Draw, Away)
                try:
                    odd_value = float(str(odd).strip()) if hasattr(odd, 'strip') else float(odd)
                    odds.append(odd_value)
                except (ValueError, TypeError):
                    continue
            
            if len(odds) >= 3:
                # Extract match date/time if available
                date_element = match_element.find('span', class_='match-time') or \
                              match_element.find('div', class_='match-date')
                match_date = date_element.text.strip() if date_element else datetime.now().strftime('%Y-%m-%d')
                
                # Extract league information if available
                league_element = match_element.find_parent().find('h3') or \
                               match_element.find('span', class_='league-name')
                league = league_element.text.strip() if league_element else "Unknown League"
                
                return {
                    'league': league,
                    'home_team': home_team,
                    'away_team': away_team,
                    'home_odds': odds[0],
                    'draw_odds': odds[1],
                    'away_odds': odds[2],
                    'match_date': match_date,
                    'scraped_at': datetime.now().isoformat(),
                    'source': 'bet9ja.com'
                }
        except Exception as e:
            logging.warning(f"Error parsing match: {e}")
        return None

    def scrape_football_page(self, page_url):
        """Scrape a specific football page for odds"""
        logging.info(f"Scraping: {page_url}")
        content = self.get_page_content(page_url)
        
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        matches = []
        
        # Common selectors for bet9ja match elements
        match_selectors = [
            'div[class*="match"]',
            'tr[class*="match"]',
            'div[class*="event"]',
            'div[class*="game"]',
            '.sport-event',
            '.match-row'
        ]
        
        for selector in match_selectors:
            match_elements = soup.select(selector)
            if match_elements:
                logging.info(f"Found {len(match_elements)} potential matches with selector: {selector}")
                break
        else:
            # Fallback: look for any elements containing team names and odds
            match_elements = soup.find_all('div', text=lambda text: text and 'vs' in text.lower())
        
        for match_element in match_elements:
            match_data = self.parse_match_odds(match_element)
            if match_data:
                matches.append(match_data)
        
        logging.info(f"Successfully parsed {len(matches)} matches from {page_url}")
        return matches

    def scrape_multiple_leagues(self, league_urls):
        """Scrape multiple league pages"""
        all_matches = []
        
        for i, url in enumerate(league_urls):
            logging.info(f"Processing league {i+1}/{len(league_urls)}: {url}")
            matches = self.scrape_football_page(url)
            all_matches.extend(matches)
            
            # Be respectful to the server
            time.sleep(2)
        
        return all_matches

    def save_to_csv(self, matches, filename=None):
        """Save matches data to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bet9ja_odds_{timestamp}.csv'
        
        if not matches:
            logging.warning("No matches to save")
            return
        
        df = pd.DataFrame(matches)
        df.to_csv(filename, index=False)
        logging.info(f"Saved {len(matches)} matches to {filename}")
        return filename

    def save_to_json(self, matches, filename=None):
        """Save matches data to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'bet9ja_odds_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(matches, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(matches)} matches to {filename}")
        return filename

    def get_sample_league_urls(self):
        """Return sample league URLs for bet9ja.com"""
        # These are example URLs - you'll need to update with actual bet9ja URLs
        return [
            "https://www.bet9ja.com/Sport/Football/England/Premier-League",
            "https://www.bet9ja.com/Sport/Football/Spain/La-Liga",
            "https://www.bet9ja.com/Sport/Football/Italy/Serie-A",
            "https://www.bet9ja.com/Sport/Football/Germany/Bundesliga",
            "https://www.bet9ja.com/Sport/Football/France/Ligue-1",
            "https://www.bet9ja.com/Sport/Football/Nigeria/NPFL",
            "https://www.bet9ja.com/Sport/Football/Champions-League",
            "https://www.bet9ja.com/Sport/Football/Europa-League",
        ]

def main():
    """Main execution function"""
    scraper = Bet9jaScraper()
    
    # Option 1: Use sample URLs
    league_urls = scraper.get_sample_league_urls()
    
    # Option 2: Load URLs from file
    # You can create a file called 'league_urls.txt' with one URL per line
    urls_file = 'league_urls.txt'
    if os.path.exists(urls_file):
        with open(urls_file, 'r') as f:
            league_urls = [line.strip() for line in f if line.strip()]
        logging.info(f"Loaded {len(league_urls)} URLs from {urls_file}")
    
    # Scrape all leagues
    logging.info(f"Starting scraping of {len(league_urls)} leagues")
    all_matches = scraper.scrape_multiple_leagues(league_urls)
    
    if all_matches:
        # Save data
        csv_file = scraper.save_to_csv(all_matches)
        json_file = scraper.save_to_json(all_matches)
        
        print(f"\n✅ Scraping completed!")
        print(f"📊 Total matches found: {len(all_matches)}")
        print(f"💾 Data saved to:")
        print(f"   - CSV: {csv_file}")
        print(f"   - JSON: {json_file}")
        
        # Display sample of scraped data
        print(f"\n📋 Sample of scraped data:")
        for i, match in enumerate(all_matches[:5]):
            print(f"{i+1}. {match['home_team']} vs {match['away_team']}")
            print(f"   Odds: {match['home_odds']} | {match['draw_odds']} | {match['away_odds']}")
            print(f"   League: {match['league']}")
    else:
        print("❌ No matches found. Please check the URLs and website structure.")

class ScheduledScraper:
    """Class for scheduling regular scraping"""
    
    def __init__(self, scraper, league_urls, interval_hours=24):
        self.scraper = scraper
        self.league_urls = league_urls
        self.interval_hours = interval_hours
        self.historical_data = []
    
    def run_daily_scrape(self):
        """Run the scraping process and store historical data"""
        timestamp = datetime.now()
        logging.info(f"Running scheduled scrape at {timestamp}")
        
        matches = self.scraper.scrape_multiple_leagues(self.league_urls)
        
        if matches:
            # Add timestamp to each match
            for match in matches:
                match['scrape_session'] = timestamp.isoformat()
            
            self.historical_data.extend(matches)
            
            # Save daily data
            date_str = timestamp.strftime('%Y%m%d')
            csv_file = self.scraper.save_to_csv(matches, f'daily_odds_{date_str}.csv')
            
            # Save cumulative historical data
            if self.historical_data:
                self.scraper.save_to_csv(self.historical_data, 'historical_odds_all.csv')
            
            logging.info(f"Daily scrape completed: {len(matches)} matches")
            return matches
        else:
            logging.warning("No matches found in daily scrape")
            return []
    
    def analyze_odds_changes(self):
        """Analyze odds changes over time"""
        if len(self.historical_data) < 2:
            logging.warning("Not enough historical data for analysis")
            return
        
        df = pd.DataFrame(self.historical_data)
        
        # Group by match (home_team + away_team) and analyze changes
        analysis = []
        for match_key, group in df.groupby(['home_team', 'away_team']):
            if len(group) >= 2:
                group_sorted = group.sort_values('scrape_session')
                initial = group_sorted.iloc[0]
                latest = group_sorted.iloc[-1]
                
                home_change = ((latest['home_odds'] - initial['home_odds']) / initial['home_odds']) * 100
                draw_change = ((latest['draw_odds'] - initial['draw_odds']) / initial['draw_odds']) * 100
                away_change = ((latest['away_odds'] - initial['away_odds']) / initial['away_odds']) * 100
                
                analysis.append({
                    'home_team': match_key[0],
                    'away_team': match_key[1],
                    'initial_home': initial['home_odds'],
                    'latest_home': latest['home_odds'],
                    'home_change_pct': home_change,
                    'initial_draw': initial['draw_odds'],
                    'latest_draw': latest['draw_odds'],
                    'draw_change_pct': draw_change,
                    'initial_away': initial['away_odds'],
                    'latest_away': latest['away_odds'],
                    'away_change_pct': away_change,
                    'days_tracked': (pd.to_datetime(latest['scrape_session']) - pd.to_datetime(initial['scrape_session'])).days
                })
        
        if analysis:
            analysis_df = pd.DataFrame(analysis)
            analysis_file = f'odds_analysis_{datetime.now().strftime("%Y%m%d")}.csv'
            analysis_df.to_csv(analysis_file, index=False)
            logging.info(f"Saved odds analysis to {analysis_file}")
            return analysis_df
        
        return None

# Automation script for Windows Task Scheduler or Linux Cron
def create_automation_script():
    """Create a batch/shell script for automation"""
    
    # Windows batch script
    batch_content = """@echo off
cd /d "%~dp0"
python bet9ja_scraper.py
pause
"""
    
    with open('run_scraper.bat', 'w') as f:
        f.write(batch_content)
    
    # Linux shell script
    shell_content = """#!/bin/bash
cd "$(dirname "$0")"
python3 bet9ja_scraper.py
"""
    
    with open('run_scraper.sh', 'w') as f:
        f.write(shell_content)
    
    # Make shell script executable (Linux/Mac)
    try:
        os.chmod('run_scraper.sh', 0o755)
    except:
        pass
    
    print("✅ Created automation scripts:")
    print("   - Windows: run_scraper.bat")
    print("   - Linux/Mac: run_scraper.sh")

# Configuration file creator
def create_config_file():
    """Create a configuration file for easy customization"""
    config = {
        "league_urls": [
            "https://www.bet9ja.com/Sport/Football/England/Premier-League",
            "https://www.bet9ja.com/Sport/Football/Spain/La-Liga",
            "https://www.bet9ja.com/Sport/Football/Italy/Serie-A",
            "https://www.bet9ja.com/Sport/Football/Germany/Bundesliga",
            "https://www.bet9ja.com/Sport/Football/France/Ligue-1",
            "https://www.bet9ja.com/Sport/Football/Nigeria/NPFL"
        ],
        "scraping_settings": {
            "delay_between_requests": 2,
            "max_retries": 3,
            "timeout": 15
        },
        "output_settings": {
            "save_csv": True,
            "save_json": True,
            "save_historical": True
        }
    }
    
    with open('scraper_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Created configuration file: scraper_config.json")
    print("   Edit this file to customize URLs and settings")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            create_config_file()
            create_automation_script()
            print("\n🚀 Setup complete! Next steps:")
            print("1. Edit scraper_config.json with your league URLs")
            print("2. Run: python bet9ja_scraper.py")
            print("3. For automation, use run_scraper.bat (Windows) or run_scraper.sh (Linux)")
            
        elif command == "config":
            create_config_file()
            
        elif command == "scripts":
            create_automation_script()
            
        else:
            print("Unknown command. Available commands: setup, config, scripts")
    else:
        main()