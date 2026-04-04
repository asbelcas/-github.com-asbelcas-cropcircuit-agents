#!/usr/bin/env python3
"""
GHOST AGENT DEBUGGER
Screenshots and analyzes Learn & Earn page structure
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

os.chdir('/home/asbelcas/rm-qpt')

# Setup logging and screenshot directory
os.makedirs('logs/screenshots', exist_ok=True)
log_file = open('logs/debug.log', 'a')

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    log_file.write(line + "\n")
    log_file.flush()

log("="*70)
log("🔍 GHOST AGENT DEBUGGER STARTING")
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
    log(f"✅ Connected: {driver.current_url}")
except Exception as e:
    log(f"❌ Connection failed: {e}")
    sys.exit(1)

def take_screenshot(name):
    """Take screenshot and save"""
    try:
        filename = f"logs/screenshots/{name}_{datetime.now().strftime('%H%M%S')}.png"
        driver.save_screenshot(filename)
        log(f"📸 Screenshot saved: {filename}")
        return filename
    except Exception as e:
        log(f"❌ Screenshot failed: {e}")
        return None

def analyze_page():
    """Analyze current page structure"""
    log("\n" + "="*70)
    log("ANALYZING LEARN & EARN PAGE")
    log("="*70)
    
    # Navigate to Learn & Earn
    log("Navigating to /earn...")
    driver.get("https://www.coinbase.com/earn")
    time.sleep(5)
    
    log(f"Page title: {driver.title}")
    log(f"Current URL: {driver.current_url}")
    
    # Take initial screenshot
    take_screenshot("01_earn_page_initial")
    
    # Scroll to load dynamic content
    log("Scrolling to load dynamic content...")
    for i in range(3):
        driver.execute_script(f"window.scrollTo(0, {i * 500})")
        time.sleep(2)
    take_screenshot("02_earn_page_scrolled")
    
    # Try multiple selectors
    log("\n--- TESTING SELECTORS ---")
    
    selectors = {
        "Links containing /earn/": "//a[contains(@href, '/earn/')]",
        "Links containing 'lesson'": "//a[contains(@href, 'lesson')]",
        "Divs with 'earn' class": "//div[contains(@class, 'earn')]",
        "Divs with 'lesson' class": "//div[contains(@class, 'lesson')]",
        "Elements with 'Earn $' text": "//*[contains(text(), 'Earn $')]",
        "Buttons with 'Start'": "//button[contains(text(), 'Start')]",
        "Cards": "//div[contains(@class, 'card')]",
        "Articles": "//article",
        "Main content sections": "//main//section",
        "Data-testid attributes": "//*[@data-testid]",
        "Any link": "//a[@href]",
        "H2 headings": "//h2",
        "H3 headings": "//h3",
    }
    
    results = {}
    for name, xpath in selectors.items():
        try:
            elements = driver.find_elements(By.XPATH, xpath)
            results[name] = len(elements)
            log(f"  {name}: {len(elements)} found")
            
            # Log first few elements if found
            if len(elements) > 0 and len(elements) <= 5:
                for i, elem in enumerate(elements[:3]):
                    try:
                        text = elem.text[:50] if elem.text else "(no text)"
                        href = elem.get_attribute('href') if hasattr(elem, 'get_attribute') else ""
                        log(f"    [{i}] {text} {href}")
                    except:
                        pass
        except Exception as e:
            log(f"  {name}: ERROR - {e}")
            results[name] = -1
    
    # Save results
    with open('logs/selector_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Get page source sample
    log("\n--- PAGE SOURCE SAMPLE ---")
    page_source = driver.page_source
    log(f"Total page length: {len(page_source)} characters")
    
    # Look for key terms
    keywords = ['earn', 'lesson', 'reward', 'learn', 'crypto', 'available', 'complete']
    log("\nKeyword occurrences:")
    for keyword in keywords:
        count = page_source.lower().count(keyword)
        log(f"  '{keyword}': {count} times")
    
    # Extract potential lesson titles
    log("\n--- POTENTIAL LESSON ELEMENTS ---")
    try:
        # Try to get all text from the page
        body_text = driver.find_element(By.TAG_NAME, 'body').text
        lines = [l.strip() for l in body_text.split('\n') if l.strip() and len(l.strip()) > 10]
        
        log(f"Found {len(lines)} text lines")
        log("First 20 lines:")
        for i, line in enumerate(lines[:20]):
            log(f"  {i+1}. {line[:80]}")
    except Exception as e:
        log(f"Error extracting text: {e}")
    
    # Final screenshot
    take_screenshot("03_earn_page_final")
    
    log("\n" + "="*70)
    log("DEBUG COMPLETE")
    log("="*70)
    log("Check logs/screenshots/ for images")
    log("Check logs/selector_results.json for data")

# Run analysis
analyze_page()

log_file.close()
