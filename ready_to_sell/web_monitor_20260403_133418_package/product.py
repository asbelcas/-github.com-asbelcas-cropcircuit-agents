#!/usr/bin/env python3
"""
Website Monitor - Uptime & Change Detection Tool
Monitors websites for downtime and content changes.
"""

import requests
import time
import hashlib
from datetime import datetime

def check_website(url, expected_text=None):
    """Check if website is up and contains expected text"""
    try:
        response = requests.get(url, timeout=30)
        status = response.status_code == 200
        
        if expected_text and expected_text not in response.text:
            return False, f"Expected text not found"
        
        return status, f"Status: {response.status_code}"
    except Exception as e:
        return False, str(e)

def monitor_loop(url, interval=300):
    """Continuously monitor a website"""
    print(f"Monitoring {url} every {interval} seconds...")
    
    while True:
        status, msg = check_website(url)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if status:
            print(f"[{timestamp}] ✅ UP - {msg}")
        else:
            print(f"[{timestamp}] ❌ DOWN - {msg}")
        
        time.sleep(interval)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        check_website(sys.argv[1])
    else:
        print("Usage: python web_monitor.py <url>")
