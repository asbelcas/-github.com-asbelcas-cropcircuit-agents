#!/usr/bin/env python3
"""
GHOST AGENT WORKER - ACTUAL WORKING AUTOMATION
No heredocs, no bash tricks - just a real Python script
"""

import sys
import time
import json
import os
from datetime import datetime, timedelta

# Change to script directory
os.chdir('/home/asbelcas/rm-qpt')

# Setup simple logging to file
log_file = open('/home/asbelcas/rm-qpt/logs/ghost_worker.log', 'a')
def log(msg):
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file.write(line + "\n")
    log_file.flush()

log("="*70)
log("👻 GHOST AGENT WORKER - STARTING")
log("="*70)

# Import selenium
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    log("✅ Selenium imported")
except Exception as e:
    log(f"❌ Selenium import failed: {e}")
    sys.exit(1)

# Connect to Chrome
log("Connecting to Chrome on port 9222...")
try:
    options = Options()
    options.add_experimental_option('debuggerAddress', '127.0.0.1:9222')
    driver = webdriver.Chrome(options=options)
    current_url = driver.current_url
    log(f"✅ Connected! URL: {current_url}")
except Exception as e:
    log(f"❌ Failed to connect: {e}")
    sys.exit(1)

# Session tracking
session_start = datetime.now()
session_end = session_start + timedelta(hours=12)
stats = {'checks': 0, 'errors': 0}

log(f"Session start: {session_start.strftime('%H:%M:%S')}")
log(f"Session end: {session_end.strftime('%H:%M:%S')}")
log(f"Duration: 12 hours")
log("="*70)

# Main monitoring loop
log("Starting monitoring loop...")
log("Press Ctrl+C to stop")
log("")

try:
    while datetime.now() < session_end:
        now = datetime.now()
        remaining = session_end - now
        
        stats['checks'] += 1
        
        try:
            # Verify Chrome connection
            current_url = driver.current_url
            
            log(f"Check #{stats['checks']} | Remaining: {remaining.seconds//3600}h {(remaining.seconds//60)%60}m | URL: {current_url[:50]}")
            
            # Save state
            state = {
                'timestamp': now.isoformat(),
                'session_start': session_start.isoformat(),
                'session_end': session_end.isoformat(),
                'stats': stats,
                'url': current_url
            }
            
            with open('/home/asbelcas/rm-qpt/logs/worker_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            
        except Exception as e:
            stats['errors'] += 1
            log(f"⚠️ Error: {e}")
        
        # Sleep 5 minutes
        time.sleep(300)
        
except KeyboardInterrupt:
    log("\n🛑 Stopped by user")
except Exception as e:
    log(f"\n❌ Fatal error: {e}")
finally:
    log("\n" + "="*70)
    log("SESSION COMPLETE")
    log("="*70)
    log(f"Total checks: {stats['checks']}")
    log(f"Errors: {stats['errors']}")
    log(f"Runtime: {datetime.now() - session_start}")
    log_file.close()
