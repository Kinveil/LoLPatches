import json
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def fetch_patch_schedule():
    """Fetch and parse the patch schedule from Riot's support page"""
    url = 'https://support-leagueoflegends.riotgames.com/hc/en-us/articles/360018987893-Patch-Schedule-League-of-Legends'
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-software-rasterizer')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        # Initialize the driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Get the page
        driver.get(url)
        
        # Get the page source
        page_source = driver.page_source
        
        # Close the driver
        driver.quit()
        
        # Parse HTML
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Find the table containing patch schedule
        table = soup.find('table')
        if not table:
            raise Exception("Couldn't find patch schedule table")
        
        patch_schedule = []
        
        # Parse table rows
        for row in table.find_all('tr')[1:]:  # Skip header row
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                patch = cells[0].get_text().strip()
                date_str = cells[1].get_text().strip()
                
                # Clean up the patch number
                patch = re.sub(r'\s+', '', patch)
                
                # Extract date and handle cases with "(Thursday)" notation
                date_str = re.sub(r'\s*\([^)]*\)', '', date_str).strip()
                
                try:
                    # Parse date - handle both formats
                    try:
                        date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    except ValueError:
                        date_obj = datetime.strptime(date_str, '%B %d %Y')
                    
                    patch_schedule.append((patch, date_obj.strftime('%Y-%m-%d')))
                except ValueError as e:
                    print(f"Warning: Could not parse date '{date_str}' for patch {patch}: {e}")
                    continue
        
        return patch_schedule
        
    except Exception as e:
        print(f"Error during web scraping: {e}")
        raise

def create_patch_data():
    """Create the complete patch data structure with timestamps and region shifts"""
    try:
        patch_schedule = fetch_patch_schedule()
    except Exception as e:
        print(f"Error fetching patch schedule: {e}")
        return None

    # Convert dates to timestamps
    patches = []
    pacific = pytz.timezone('America/Los_Angeles')
    
    for patch, date_str in patch_schedule:
        # Parse the date and set to 1 PM Pacific time (usual patch time)
        naive_date = datetime.strptime(date_str, '%Y-%m-%d')
        pacific_date = pacific.localize(naive_date.replace(hour=13))  # 1 PM Pacific
        utc_date = pacific_date.astimezone(pytz.UTC)
        timestamp = int(utc_date.timestamp())
        
        patches.append({
            'name': patch,
            'start': timestamp
        })

    # Sort patches by timestamp
    patches.sort(key=lambda x: x['start'])

    # Region shifts in seconds
    shifts = {
        'OC1': -46800,
        'JP1': -43200,
        'KR': -39600,
        'RU': -28800,
        'EUN1': -21600,
        'TR1': -18000,
        'EUW1': -10800,
        'BR1': -3600,
        'LA2': 0,
        'LA1': 7200,
        'NA1': 10800,
        'PH': 43200,
        'ID1': 43200,
        'VN': 46800,
        'SG': 50400,
        'TH': 54000,
        'TW': 57600
    }

    patch_data = {
        'patches': patches,
        'shifts': shifts
    }

    return patch_data

def main():
    # Fetch and process patch data
    patch_data = create_patch_data()
    
    if patch_data:
        # Save to JSON file
        with open('patches.json', 'w') as f:
            json.dump(patch_data, f, indent=2)
        print(f"Successfully processed {len(patch_data['patches'])} patches")
        
        # Print the patches for verification
        for patch in patch_data['patches']:
            patch_time = datetime.fromtimestamp(patch['start'], pytz.UTC)
            print(f"{patch['name']}: {patch_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    else:
        print("Failed to create patch data")
        exit(1)

if __name__ == '__main__':
    main()
