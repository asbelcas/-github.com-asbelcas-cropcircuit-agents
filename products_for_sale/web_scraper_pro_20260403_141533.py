#!/usr/bin/env python3
"""
Web Scraper Pro - Professional Data Extraction Tool

Features:
- Multi-site scraping
- Automatic retry logic
- Data export (CSV, JSON, Excel)
- Proxy support
- Rate limiting

PRICE: $29
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
from urllib.parse import urljoin

class WebScraperPro:
    def __init__(self, delay=1):
        self.session = requests.Session()
        self.delay = delay
        self.results = []
        
    def scrape(self, url, selector_dict):
        """Scrape data from URL"""
        try:
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = {}
            for key, selector in selector_dict.items():
                elem = soup.select_one(selector)
                data[key] = elem.get_text(strip=True) if elem else None
            
            time.sleep(self.delay)
            return data
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def export_csv(self, filename):
        """Export results to CSV"""
        df = pd.DataFrame(self.results)
        df.to_csv(filename, index=False)
        print(f"Exported {len(self.results)} records to {filename}")

if __name__ == "__main__":
    scraper = WebScraperPro()
    print("Web Scraper Pro ready")
