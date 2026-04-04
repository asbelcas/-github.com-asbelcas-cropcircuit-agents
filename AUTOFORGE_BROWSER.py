#!/usr/bin/env python3
"""
AUTOFORGE-LITE - BROWSER AUTOMATION MODULE
Real submission to Upwork/Fiverr via Selenium

⚠️  WARNING: Using browser automation on freelance platforms violates their Terms of Service.
⚠️  Your account may be suspended or banned.
⚠️  Use at your own risk.
"""

import os
import sys
import time
import json
import random
from datetime import datetime
from pathlib import Path

# Selenium imports
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
        ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("❌ Selenium not installed. Run: pip install selenium")
    sys.exit(1)

class PlatformBrowser:
    """Browser automation for freelance platforms"""
    
    def __init__(self, platform="upwork"):
        self.platform = platform
        self.driver = None
        self.wait = None
        self.logged_in = False
        self.log_file = f"/home/asbelcas/rm-qpt/logs/browser_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        os.makedirs("/home/asbelcas/rm-qpt/logs", exist_ok=True)
        
    def _log(self, message):
        """Log browser activity"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        print(line)
        with open(self.log_file, 'a') as f:
            f.write(line + "\n")
    
    def _init_driver(self):
        """Initialize Chrome with anti-detection"""
        self._log("Initializing Chrome browser...")
        
        options = Options()
        
        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Standard options
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        # Random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            self._log("✅ Browser initialized")
            return True
        except Exception as e:
            self._log(f"❌ Browser init failed: {e}")
            return False
    
    def _human_like_delay(self, min_sec=2, max_sec=5):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
    
    def _human_like_typing(self, element, text):
        """Type like a human with random delays"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _safe_find_element(self, by, value, timeout=10):
        """Safely find element with retry"""
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None
    
    def login_upwork(self, email, password):
        """Login to Upwork"""
        self._log("Navigating to Upwork login...")
        
        try:
            self.driver.get("https://www.upwork.com/ab/account-security/login")
            self._human_like_delay(3, 5)
            
            # Check if already logged in
            if "find-work" in self.driver.current_url or "dashboard" in self.driver.current_url:
                self._log("✅ Already logged in")
                self.logged_in = True
                return True
            
            # Find email field
            email_field = self._safe_find_element(By.ID, "login_username")
            if not email_field:
                # Try alternative selectors
                email_field = self._safe_find_element(By.CSS_SELECTOR, "input[type='email']")
            
            if email_field:
                self._log("Entering email...")
                email_field.click()
                self._human_like_delay(0.5, 1)
                self._human_like_typing(email_field, email)
                self._human_like_delay(1, 2)
                
                # Click continue
                continue_btn = self._safe_find_element(By.CSS_SELECTOR, "button[data-test='continue-next']")
                if continue_btn:
                    continue_btn.click()
                    self._human_like_delay(2, 4)
                
                # Find password field
                password_field = self._safe_find_element(By.ID, "login_password")
                if not password_field:
                    password_field = self._safe_find_element(By.CSS_SELECTOR, "input[type='password']")
                
                if password_field:
                    self._log("Entering password...")
                    password_field.click()
                    self._human_like_delay(0.5, 1)
                    self._human_like_typing(password_field, password)
                    self._human_like_delay(1, 2)
                    
                    # Click login
                    login_btn = self._safe_find_element(By.CSS_SELECTOR, "button[data-test='login-submit']")
                    if login_btn:
                        login_btn.click()
                        self._human_like_delay(5, 8)
                        
                        # Check for 2FA
                        if "enter-code" in self.driver.current_url or "security-question" in self.driver.current_url:
                            self._log("⏸️ 2FA/Security check required - Human intervention needed")
                            self._save_checkpoint("upwork_2fa", "2FA required", {
                                "url": self.driver.current_url,
                                "action": "Enter 2FA code and click verify"
                            })
                            return False
                        
                        # Check login success
                        if "find-work" in self.driver.current_url or "dashboard" in self.driver.current_url:
                            self._log("✅ Login successful")
                            self.logged_in = True
                            return True
                        else:
                            self._log(f"❌ Login failed. Current URL: {self.driver.current_url}")
                            return False
                else:
                    self._log("❌ Password field not found")
                    return False
            else:
                self._log("❌ Email field not found")
                return False
                
        except Exception as e:
            self._log(f"❌ Login error: {e}")
            return False
    
    def find_jobs_upwork(self, keywords="python automation"):
        """Find jobs on Upwork"""
        self._log(f"Searching for jobs: {keywords}")
        
        try:
            # Navigate to job search
            search_url = f"https://www.upwork.com/nx/jobs/search/?q={keywords.replace(' ', '%20')}&sort=recency"
            self.driver.get(search_url)
            self._human_like_delay(5, 8)
            
            # Check for CAPTCHA
            if "captcha" in self.driver.page_source.lower() or "recaptcha" in self.driver.page_source.lower():
                self._log("⏸️ CAPTCHA detected - Human intervention required")
                self._save_checkpoint("upwork_captcha", "CAPTCHA detected", {
                    "url": self.driver.current_url,
                    "action": "Solve CAPTCHA manually"
                })
                return []
            
            # Find job cards
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "article[data-test='JobTile']")
            
            if not job_cards:
                # Try alternative selector
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='job-tile']")
            
            self._log(f"Found {len(job_cards)} job cards")
            
            jobs = []
            for card in job_cards[:5]:  # Top 5 jobs
                try:
                    title_elem = card.find_element(By.CSS_SELECTOR, "h2 a, .job-title a")
                    title = title_elem.text
                    link = title_elem.get_attribute("href")
                    
                    budget_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-budget'], .budget")
                    budget = budget_elem.text if budget_elem else "Not specified"
                    
                    jobs.append({
                        "title": title,
                        "link": link,
                        "budget": budget,
                        "platform": "upwork"
                    })
                except:
                    continue
            
            return jobs
            
        except Exception as e:
            self._log(f"❌ Job search error: {e}")
            return []
    
    def submit_proposal_upwork(self, job_link, proposal_text, cover_letter):
        """Submit proposal to a job"""
        self._log(f"Submitting proposal to: {job_link}")
        
        try:
            # Navigate to job
            self.driver.get(job_link)
            self._human_like_delay(5, 8)
            
            # Check if already applied
            if "you have already submitted a proposal" in self.driver.page_source.lower():
                self._log("⚠️ Already applied to this job")
                return False
            
            # Find apply button
            apply_btn = self._safe_find_element(By.CSS_SELECTOR, "button[data-test='apply-button'], .apply-button")
            if not apply_btn:
                apply_btn = self._safe_find_element(By.XPATH, "//button[contains(text(), 'Apply')]")
            
            if apply_btn:
                self._log("Clicking apply button...")
                apply_btn.click()
                self._human_like_delay(5, 10)
                
                # Check for proposal form
                cover_letter_field = self._safe_find_element(By.CSS_SELECTOR, "textarea[data-test='cover-letter'], #coverLetter")
                
                if cover_letter_field:
                    self._log("Entering cover letter...")
                    cover_letter_field.click()
                    self._human_like_delay(1, 2)
                    self._human_like_typing(cover_letter_field, cover_letter)
                    self._human_like_delay(2, 4)
                    
                    # Find submit button
                    submit_btn = self._safe_find_element(By.CSS_SELECTOR, "button[data-test='submit-proposal'], #submit-proposal")
                    if submit_btn:
                        # ⚠️ CRITICAL: This is where we STOP for approval
                        self._log("⏸️ PROPOSAL READY FOR SUBMISSION")
                        self._log("⚠️  Human approval required before final submit")
                        
                        # Save checkpoint for human approval
                        self._save_checkpoint("upwork_submit", "Proposal ready - approve submission?", {
                            "job_link": job_link,
                            "proposal_text": proposal_text,
                            "cover_letter": cover_letter,
                            "action": "Review proposal then click submit button"
                        })
                        
                        return "CHECKPOINT_CREATED"
                    else:
                        self._log("❌ Submit button not found")
                        return False
                else:
                    self._log("❌ Cover letter field not found")
                    return False
            else:
                self._log("❌ Apply button not found")
                return False
                
        except Exception as e:
            self._log(f"❌ Submission error: {e}")
            return False
    
    def _save_checkpoint(self, task_id, reason, data):
        """Save checkpoint for human approval"""
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "reason": reason,
            "data": data,
            "platform": self.platform,
            "url": self.driver.current_url if self.driver else None
        }
        
        checkpoint_file = f"/home/asbelcas/rm-qpt/checkpoints/browser_{task_id}_{int(time.time())}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
        
        self._log(f"💾 Checkpoint saved: {checkpoint_file}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self._log("Closing browser...")
            self.driver.quit()

class BrowserSubmissionManager:
    """Manager for browser-based submissions"""
    
    def __init__(self):
        self.upwork_browser = None
        self.fiverr_browser = None
        
    def submit_to_upwork(self, opportunity, proposal_text):
        """
        Submit proposal to Upwork with full browser automation
        Stops at final submission for human approval
        """
        print("="*70)
        print("🌐 UPWORK BROWSER SUBMISSION")
        print("="*70)
        print()
        print("⚠️  WARNING: This will automate browser actions on Upwork")
        print("⚠️  Your account may be flagged or suspended")
        print("⚠️  Use at your own risk")
        print()
        
        # Get credentials
        email = input("Enter Upwork email: ")
        password = input("Enter Upwork password: ")
        
        # Initialize browser
        browser = PlatformBrowser("upwork")
        if not browser._init_driver():
            print("❌ Failed to initialize browser")
            return False
        
        # Login
        if not browser.login_upwork(email, password):
            print("❌ Login failed or requires 2FA")
            browser.close()
            return False
        
        # Navigate to job and prepare proposal
        result = browser.submit_proposal_upwork(
            opportunity.get('link', ''),
            proposal_text,
            proposal_text  # Cover letter same as proposal for now
        )
        
        if result == "CHECKPOINT_CREATED":
            print()
            print("="*70)
            print("⏸️  CHECKPOINT: Proposal prepared, waiting for final approval")
            print("="*70)
            print()
            print("The browser is open with the proposal form filled.")
            print("REVIEW the proposal on screen.")
            print("CLICK the submit button yourself when ready.")
            print()
            print("This ensures:")
            print("  ✅ You see exactly what's being submitted")
            print("  ✅ You control the final action")
            print("  ✅ Lower risk of account ban")
            print()
            input("Press Enter when you've submitted (or Ctrl+C to cancel)...")
        
        browser.close()
        return True

def main():
    print("="*70)
    print("🌐 AUTOFORGE-LITE: Browser Automation Module")
    print("="*70)
    print()
    print("⚠️  CRITICAL WARNINGS:")
    print("   1. Browser automation violates Upwork/Fiverr Terms of Service")
    print("   2. Your account may be suspended or banned")
    print("   3. CAPTCHAs and 2FA will require human intervention")
    print("   4. Platform changes break automation constantly")
    print()
    print("RECOMMENDED: Use manual mode instead")
    print("   - System drafts proposals")
    print("   - You copy/paste and submit manually")
    print("   - Zero risk to your account")
    print()
    
    choice = input("Continue with browser automation? (yes/no): ").lower()
    
    if choice != "yes":
        print("\n✅ Smart choice. Use manual mode for safety.")
        return
    
    # Example submission
    manager = BrowserSubmissionManager()
    
    test_opportunity = {
        "link": "https://www.upwork.com/jobs/example",
        "title": "Test Job"
    }
    
    test_proposal = "Hi, I can help with this project. I have experience in Python automation."
    
    print("\n🚀 Starting browser submission...")
    manager.submit_to_upwork(test_opportunity, test_proposal)

if __name__ == "__main__":
    main()
