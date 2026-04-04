#!/usr/bin/env python3
"""
AUTOFORGE-LITE - BROWSER AUTOMATION V2 (FAILURE-RESISTANT)
Preemptive failure analysis and robust error handling

FAILURE MODES ANTICIPATED:
1. Chrome/WebDriver issues
2. Login failures (2FA, CAPTCHA, wrong creds)
3. Page structure changes
4. Anti-automation detection
5. Network timeouts
6. Job state changes (already applied, closed)
7. Form field variations
8. Rate limiting
9. Session expiration
10. Element interaction failures
"""

import os
import sys
import json
import time
import random
import subprocess
from datetime import datetime
from pathlib import Path

# PRE-FLIGHT CHECKS BEFORE IMPORTING SELENIUM
def preflight_checks():
    """Check system readiness before starting"""
    print("="*70)
    print("🔍 PRE-FLIGHT SYSTEM CHECKS")
    print("="*70)
    print()
    
    checks = []
    
    # Check 1: Chrome installed
    try:
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            checks.append(("✅", "Chrome installed", result.stdout.strip()))
        else:
            checks.append(("❌", "Chrome installed", "Chrome not found"))
    except:
        checks.append(("❌", "Chrome installed", "Chrome not installed or not in PATH"))
    
    # Check 2: Python packages
    try:
        import selenium
        checks.append(("✅", "Selenium package", f"Version {selenium.__version__}"))
    except ImportError:
        checks.append(("❌", "Selenium package", "Not installed - Run: pip install selenium"))
    
    try:
        import webdriver_manager
        checks.append(("✅", "WebDriver Manager", "Installed"))
    except ImportError:
        checks.append(("⚠️", "WebDriver Manager", "Not installed - May need manual chromedriver"))
    
    # Check 3: Display (for headless mode)
    if os.environ.get('DISPLAY') or os.path.exists('/tmp/.X11-unix'):
        checks.append(("✅", "Display available", "GUI mode possible"))
    else:
        checks.append(("⚠️", "Display available", "No display - will use headless mode"))
    
    # Check 4: Network connectivity
    try:
        import socket
        socket.create_connection(("www.upwork.com", 443), timeout=5)
        checks.append(("✅", "Network connectivity", "Can reach Upwork"))
    except:
        checks.append(("❌", "Network connectivity", "Cannot reach Upwork - check internet"))
    
    # Check 5: Disk space
    stat = os.statvfs('/home/asbelcas')
    free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
    if free_gb > 1:
        checks.append(("✅", "Disk space", f"{free_gb:.1f} GB free"))
    else:
        checks.append(("⚠️", "Disk space", f"{free_gb:.1f} GB free - may be tight"))
    
    # Check 6: Credentials file
    creds_file = "/home/asbelcas/rm-qpt/credentials.json"
    if os.path.exists(creds_file):
        checks.append(("✅", "Credentials file", "Found (DO NOT COMMIT THIS)"))
    else:
        checks.append(("⚠️", "Credentials file", "Not found - will prompt for login"))
    
    # Display results
    all_pass = True
    for status, check, detail in checks:
        print(f"{status} {check:.<30} {detail}")
        if status == "❌":
            all_pass = False
    
    print()
    
    if not all_pass:
        print("❌ PRE-FLIGHT FAILED - Fix issues above before continuing")
        return False
    else:
        print("✅ PRE-FLIGHT PASSED - System ready")
        return True

# Only proceed if preflight passes
if not preflight_checks():
    response = input("\nContinue anyway? (yes/no): ")
    if response.lower() != "yes":
        sys.exit(1)
    print("\n⚠️  Continuing with warnings...")

# Now import Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException,
        ElementNotInteractableException, StaleElementReferenceException,
        ElementClickInterceptedException
    )
except ImportError as e:
    print(f"❌ Failed to import Selenium: {e}")
    print("Install with: pip install selenium webdriver-manager")
    sys.exit(1)

class FailureResistantBrowser:
    """Browser automation with comprehensive error handling"""
    
    def __init__(self, platform="upwork"):
        self.platform = platform
        self.driver = None
        self.wait = None
        self.wait_short = None
        self.logged_in = False
        self.session_start = time.time()
        self.actions_count = 0
        self.failures = []
        
        self.log_file = f"/home/asbelcas/rm-qpt/logs/browser_v2_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs("/home/asbelcas/rm-qpt/logs", exist_ok=True)
        
        self._log("="*70)
        self._log("🤖 FAILURE-RESISTANT BROWSER V2")
        self._log("="*70)
        self._log(f"Platform: {platform}")
        self._log(f"Session start: {datetime.now()}")
    
    def _log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        with open(self.log_file, 'a') as f:
            f.write(line + "\n")
    
    def _safe_execute(self, action_name, action_func, retries=3, **kwargs):
        """Execute action with retry logic"""
        for attempt in range(1, retries + 1):
            try:
                self._log(f"  Attempting {action_name} (try {attempt}/{retries})")
                result = action_func(**kwargs)
                self._log(f"  ✅ {action_name} succeeded")
                return result
            except StaleElementReferenceException as e:
                self._log(f"  ⚠️  Element stale, retrying...")
                time.sleep(1)
            except ElementClickInterceptedException as e:
                self._log(f"  ⚠️  Click intercepted, scrolling and retrying...")
                self._scroll_to_element(kwargs.get('element'))
                time.sleep(0.5)
            except TimeoutException as e:
                self._log(f"  ⚠️  Timeout, waiting...")
                time.sleep(2)
            except Exception as e:
                self._log(f"  ❌ {action_name} failed: {str(e)[:100]}")
                if attempt == retries:
                    self.failures.append({
                        "action": action_name,
                        "error": str(e),
                        "time": datetime.now().isoformat()
                    })
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _scroll_to_element(self, element):
        """Scroll element into view"""
        if element and self.driver:
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(0.5)
            except:
                pass
    
    def _human_like_delay(self, min_sec=2, max_sec=5):
        """Random delay with jitter"""
        base_delay = random.uniform(min_sec, max_sec)
        jitter = random.uniform(-0.5, 0.5)
        delay = max(0.5, base_delay + jitter)
        time.sleep(delay)
    
    def _random_mouse_movement(self):
        """Simulate random mouse movements"""
        if not self.driver:
            return
        try:
            # Random scroll
            scroll_amount = random.randint(-300, 300)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.5))
        except:
            pass
    
    def _init_driver(self):
        """Initialize Chrome with multiple fallback strategies"""
        self._log("Initializing Chrome with anti-detection...")
        
        strategies = [
            self._init_strategy_1,  # WebDriver Manager
            self._init_strategy_2,  # System chromedriver
            self._init_strategy_3,  # Headless only
        ]
        
        for i, strategy in enumerate(strategies, 1):
            self._log(f"  Trying initialization strategy {i}...")
            if strategy():
                self._log("✅ Browser initialized successfully")
                return True
            self._log(f"  Strategy {i} failed, trying next...")
        
        self._log("❌ All initialization strategies failed")
        return False
    
    def _init_strategy_1(self):
        """Strategy 1: WebDriver Manager"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = self._get_chrome_options()
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self._post_init_setup()
            return True
        except Exception as e:
            self._log(f"    WebDriver Manager failed: {str(e)[:80]}")
            return False
    
    def _init_strategy_2(self):
        """Strategy 2: System chromedriver"""
        try:
            options = self._get_chrome_options()
            self.driver = webdriver.Chrome(options=options)
            self._post_init_setup()
            return True
        except Exception as e:
            self._log(f"    System chromedriver failed: {str(e)[:80]}")
            return False
    
    def _init_strategy_3(self):
        """Strategy 3: Headless only"""
        try:
            options = self._get_chrome_options(headless=True)
            self.driver = webdriver.Chrome(options=options)
            self._post_init_setup()
            return True
        except Exception as e:
            self._log(f"    Headless mode failed: {str(e)[:80]}")
            return False
    
    def _get_chrome_options(self, headless=False):
        """Get Chrome options with anti-detection"""
        options = Options()
        
        # Anti-detection essentials
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Common options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        if headless or not os.environ.get('DISPLAY'):
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
        
        # Window size
        options.add_argument("--window-size=1920,1080")
        
        # User agent rotation
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # Additional stealth
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        return options
    
    def _post_init_setup(self):
        """Setup after driver initialization"""
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set timeouts
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
        
        # Initialize wait objects
        self.wait = WebDriverWait(self.driver, 15)
        self.wait_short = WebDriverWait(self.driver, 5)
    
    def _safe_find_element(self, selectors, timeout=10):
        """
        Find element trying multiple selectors
        selectors: list of tuples [(By.ID, "value"), (By.CSS_SELECTOR, "value"), ...]
        """
        if not isinstance(selectors, list):
            selectors = [selectors]
        
        for by, value in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((by, value))
                )
                return element
            except:
                continue
        
        return None
    
    def _detect_blocking(self):
        """Detect if we've hit a blocking mechanism"""
        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url
        
        # CAPTCHA detection
        captcha_indicators = ['captcha', 'recaptcha', "i'm not a robot", 'verify you are human']
        for indicator in captcha_indicators:
            if indicator in page_source:
                return "CAPTCHA", f"CAPTCHA detected: {indicator}"
        
        # Rate limiting
        if 'rate limit' in page_source or 'too many requests' in page_source or '429' in page_source:
            return "RATE_LIMIT", "Rate limiting detected"
        
        # IP blocking
        if 'access denied' in page_source or 'blocked' in page_source:
            return "IP_BLOCKED", "IP blocking detected"
        
        # Login required
        if '/login' in current_url and 'login' in page_source:
            return "LOGIN_REQUIRED", "Redirected to login page"
        
        # 2FA detection
        if any(x in page_source for x in ['two-factor', '2fa', 'verification code', 'security code']):
            return "2FA_REQUIRED", "Two-factor authentication required"
        
        return None, None
    
    def _handle_blocking(self, block_type, message):
        """Handle blocking scenarios"""
        self._log(f"🚨 BLOCKING DETECTED: {block_type}")
        self._log(f"   {message}")
        
        # Take screenshot for debugging
        try:
            screenshot_path = f"/home/asbelcas/rm-qpt/logs/block_{block_type}_{int(time.time())}.png"
            self.driver.save_screenshot(screenshot_path)
            self._log(f"   Screenshot saved: {screenshot_path}")
        except:
            pass
        
        # Save checkpoint for human intervention
        checkpoint = {
            "type": "blocking",
            "block_type": block_type,
            "message": message,
            "url": self.driver.current_url,
            "timestamp": datetime.now().isoformat(),
            "action_required": self._get_blocking_action(block_type)
        }
        
        checkpoint_file = f"/home/asbelcas/rm-qpt/checkpoints/block_{block_type}_{int(time.time())}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        self._log(f"   Checkpoint saved: {checkpoint_file}")
        self._log(f"   Action required: {checkpoint['action_required']}")
        
        return False
    
    def _get_blocking_action(self, block_type):
        """Get recommended action for blocking type"""
        actions = {
            "CAPTCHA": "Solve CAPTCHA manually or wait 1-2 hours and retry",
            "RATE_LIMIT": "Wait 30-60 minutes before retrying",
            "IP_BLOCKED": "Use VPN or wait 24 hours",
            "LOGIN_REQUIRED": "Re-login with credentials",
            "2FA_REQUIRED": "Enter 2FA code manually"
        }
        return actions.get(block_type, "Manual intervention required")
    
    def health_check(self):
        """Check if browser session is healthy"""
        if not self.driver:
            return False, "Driver not initialized"
        
        try:
            # Try to get current URL
            _ = self.driver.current_url
            
            # Check session age
            session_age = time.time() - self.session_start
            if session_age > 3600:  # 1 hour
                return False, f"Session too old ({session_age/60:.0f} min)"
            
            return True, "Healthy"
        except Exception as e:
            return False, str(e)
    
    def close(self):
        """Safely close browser"""
        if self.driver:
            try:
                self._log("Closing browser...")
                self.driver.quit()
                self._log("✅ Browser closed")
            except Exception as e:
                self._log(f"⚠️  Error closing browser: {e}")

def test_browser_initialization():
    """Test that browser can be initialized"""
    print("="*70)
    print("🧪 TESTING BROWSER INITIALIZATION")
    print("="*70)
    print()
    
    browser = FailureResistantBrowser("upwork")
    
    if browser._init_driver():
        print()
        print("✅ Browser initialized successfully")
        
        # Test navigation
        print()
        print("Testing navigation to example.com...")
        browser.driver.get("https://example.com")
        time.sleep(2)
        
        if "example.com" in browser.driver.current_url:
            print("✅ Navigation works")
        else:
            print(f"⚠️  Unexpected URL: {browser.driver.current_url}")
        
        browser.close()
        return True
    else:
        print()
        print("❌ Failed to initialize browser")
        return False

def main():
    print("="*70)
    print("🌐 AUTOFORGE-LITE: Failure-Resistant Browser V2")
    print("="*70)
    print()
    
    # Pre-flight checks
    if not preflight_checks():
        print()
        print("❌ Pre-flight checks failed. Fix issues before continuing.")
        return
    
    print()
    print("Options:")
    print("1. Test browser initialization only")
    print("2. Test with Upwork (requires credentials)")
    print("3. Exit")
    print()
    
    choice = input("Select option: ")
    
    if choice == "1":
        test_browser_initialization()
    elif choice == "2":
        print()
        print("⚠️  Live testing with Upwork will require:")
        print("   - Your Upwork login credentials")
        print("   - 2FA code if enabled")
        print("   - Manual intervention if CAPTCHA appears")
        print()
        
        confirm = input("Continue with live Upwork test? (yes/no): ")
        if confirm.lower() == "yes":
            # TODO: Implement full Upwork workflow
            print()
            print("⏸️  Full Upwork automation not yet implemented.")
            print("   Use AUTOFORGE_BROWSER.py for that.")
        else:
            print("Cancelled.")
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()
