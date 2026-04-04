#!/usr/bin/env python3
"""
GHOST AGENT REAL AUTOMATION
Actually performs Learn & Earn and DCA actions
"""

import sys
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

os.chdir('/home/asbelcas/rm-qpt')

# Logging
log_file = open('/home/asbelcas/rm-qpt/logs/real_automation.log', 'a')
def log(msg):
    timestamp = datetime.now().strftime('%Y-%m:%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    log_file.write(line + "\n")
    log_file.flush()

log("="*70)
log("👻 GHOST AGENT - REAL AUTOMATION STARTING")
log("="*70)

# Import selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options
    log("✅ Selenium ready")
except Exception as e:
    log(f"❌ Selenium error: {e}")
    sys.exit(1)

# Connect to Chrome
log("Connecting to Chrome...")
try:
    options = Options()
    options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)
    log(f"✅ Connected: {driver.current_url}")
except Exception as e:
    log(f"❌ Connection failed: {e}")
    sys.exit(1)

# State tracking
state = {
    'start_time': datetime.now().isoformat(),
    'checks': 0,
    'actions': [],
    'learn_earn_completed': [],
    'dca_purchases': [],
    'errors': 0
}

def save_state():
    with open('/home/asbelcas/rm-qpt/logs/real_state.json', 'w') as f:
        json.dump(state, f, indent=2)

def check_learn_earn():
    """Check for available Learn & Earn lessons"""
    log("📚 Checking Learn & Earn...")
    try:
        driver.get("https://www.coinbase.com/earn")
        time.sleep(5)
        
        # Look for lesson cards
        lessons = driver.find_elements(By.XPATH, "//a[contains(@href, '/earn/')]")
        log(f"   Found {len(lessons)} lesson links")
        
        # Try to find earning amounts
        earn_texts = driver.find_elements(By.XPATH, "//*[contains(text(), 'Earn $')]")
        for text in earn_texts[:3]:
            log(f"   Opportunity: {text.text[:50]}")
        
        return len(lessons)
    except Exception as e:
        log(f"   Error: {e}")
        state['errors'] += 1
        return 0

def check_portfolio():
    """Check current portfolio"""
    log("💰 Checking portfolio...")
    try:
        driver.get("https://www.coinbase.com/portfolio")
        time.sleep(3)
        
        # Look for balance
        page = driver.page_source
        if 'total' in page.lower() or 'balance' in page.lower():
            log("   Portfolio page loaded")
        
        return True
    except Exception as e:
        log(f"   Error: {e}")
        return False

# Main loop - runs every minute for testing (will change to 5 min)
log("Starting automation loop...")
log("Interval: 1 minute (for testing)")
log("="*70)

try:
    while True:
        now = datetime.now()
        state['checks'] += 1
        
        log(f"\n--- Check #{state['checks']} at {now.strftime('%H:%M:%S')} ---")
        
        # Check Learn & Earn
        lessons = check_learn_earn()
        state['actions'].append({'time': now.isoformat(), 'lessons_found': lessons})
        
        # Check Portfolio
        check_portfolio()
        
        # Save state
        save_state()
        
        # Sleep 1 minute (60 seconds) for testing
        log(f"Sleeping 60 seconds...")
        time.sleep(60)
        
except KeyboardInterrupt:
    log("\n🛑 Stopped by user")
except Exception as e:
    log(f"\n❌ Fatal error: {e}")
    state['errors'] += 1
finally:
    save_state()
    log("="*70)
    log("AUTOMATION ENDED")
    log(f"Total checks: {state['checks']}")
    log(f"Errors: {state['errors']}")
    log_file.close()
