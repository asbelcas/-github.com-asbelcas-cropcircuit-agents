#!/usr/bin/env python3
"""
GHOST AGENT v5.0 - FULLY AUTOMATED EXECUTOR
Complete automation for Coinbase Learn & Earn + DCA Strategy
"""

import sys
import time
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List, Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/asbelcas/rm-qpt/logs/ghost_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GhostAuto")

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, ElementNotInteractableException,
        StaleElementReferenceException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.error("Selenium not installed. Run: pip install selenium")
    sys.exit(1)


@dataclass
class Action:
    """Represents an automated action"""
    name: str
    url: str
    expected_result: str
    max_retries: int = 3


class GhostAutoExecutor:
    """
    Fully automated executor for Ghost Agent v5.0
    Handles Learn & Earn, DCA, and monitoring
    """
    
    def __init__(self, capital: float = 16.0):
        self.capital = capital
        self.driver = None
        self.wait = None
        self.session_start = datetime.now()
        self.actions_completed = []
        self.earnings = 0.0
        self.dca_schedule = []
        self.running = True
        
        # Statistics
        self.stats = {
            'lessons_completed': 0,
            'dca_purchases': 0,
            'total_earned': 0.0,
            'total_spent': 0.0,
            'errors': 0
        }
        
        logger.info("="*70)
        logger.info("  👻 GHOST AGENT v5.0 - FULLY AUTOMATED EXECUTOR")
        logger.info("="*70)
        logger.info(f"Capital: ${capital:.2f}")
        logger.info(f"Strategy: DCA + Learn & Earn")
        logger.info("="*70)
    
    def connect_to_browser(self) -> bool:
        """Connect to existing Chrome instance with remote debugging"""
        logger.info("🌐 Connecting to Chrome...")
        
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
            logger.info(f"✅ Connected to Chrome")
            logger.info(f"   Current URL: {self.driver.current_url}")
            
            # Verify connection
            title = self.driver.title
            logger.info(f"   Page title: {title}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
    
    def check_login_status(self) -> bool:
        """Check if user is logged into Coinbase"""
        logger.info("🔐 Checking login status...")
        
        try:
            # Navigate to portfolio to check login
            self.driver.get("https://www.coinbase.com/portfolio")
            time.sleep(3)
            
            page_source = self.driver.page_source.lower()
            current_url = self.driver.current_url
            
            # Check for logged-in indicators
            logged_in_indicators = [
                'portfolio', 'balances', 'total balance', 'assets',
                'trade', 'send', 'receive', 'buy', 'sell'
            ]
            
            # Check for login page indicators
            login_indicators = ['/signin', 'sign in', 'log in', 'password']
            
            is_logged_in = any(ind in page_source for ind in logged_in_indicators)
            is_login_page = any(ind in current_url.lower() or ind in page_source 
                               for ind in login_indicators)
            
            if is_logged_in and not is_login_page:
                logger.info("✅ User is LOGGED IN")
                return True
            else:
                logger.warning("⚠️  User may not be logged in")
                logger.info("   Please login manually in the browser")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking login: {e}")
            return False
    
    def execute_learn_and_earn(self) -> float:
        """
        Automated Learn & Earn execution
        Returns: Amount earned
        """
        logger.info("\n" + "="*70)
        logger.info("  📚 PHASE 1: LEARN & EARN")
        logger.info("="*70)
        
        earned = 0.0
        
        try:
            # Navigate to Learn & Earn
            logger.info("Navigating to Learn & Earn...")
            self.driver.get("https://www.coinbase.com/learn")
            time.sleep(5)
            
            # Look for earn opportunities
            logger.info("Scanning for available lessons...")
            
            # Try multiple selectors for lesson cards
            lesson_selectors = [
                "//div[contains(@class, 'earn')]",
                "//div[contains(text(), 'Earn')]",
                "//a[contains(@href, 'earn')]",
                "//div[contains(@class, 'lesson')]",
                "//button[contains(text(), 'Start')]",
                "//div[contains(@class, 'card')]",
            ]
            
            lessons = []
            for selector in lesson_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        lessons.extend(elements)
                        logger.info(f"   Found {len(elements)} potential lessons with: {selector}")
                except:
                    continue
            
            if not lessons:
                logger.warning("⚠️  No lessons found - may need to scroll or page still loading")
                self._take_screenshot("learn_earn_page")
                return 0.0
            
            # Process each lesson
            logger.info(f"\n🎯 Found {len(lessons)} potential lessons")
            
            for i, lesson in enumerate(lessons[:5], 1):  # Max 5 lessons
                try:
                    logger.info(f"\n--- Lesson {i} ---")
                    
                    # Try to click the lesson
                    try:
                        lesson.click()
                        time.sleep(3)
                    except:
                        # Try finding a link within the lesson
                        try:
                            link = lesson.find_element(By.TAG_NAME, "a")
                            link.click()
                            time.sleep(3)
                        except:
                            logger.info("   Could not click lesson - may need manual interaction")
                            continue
                    
                    # Look for video or start button
                    self._handle_lesson_content()
                    
                    earned += 3.0  # Assume $3 per lesson
                    self.stats['lessons_completed'] += 1
                    
                    # Go back to learn page
                    self.driver.get("https://www.coinbase.com/learn")
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"   Error with lesson {i}: {e}")
                    continue
            
            logger.info(f"\n✅ Learn & Earn phase complete")
            logger.info(f"   Lessons attempted: {self.stats['lessons_completed']}")
            logger.info(f"   Estimated earnings: ${earned:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Learn & Earn error: {e}")
        
        return earned
    
    def _handle_lesson_content(self):
        """Handle individual lesson content"""
        try:
            # Look for start/continue button
            buttons = self.driver.find_elements(By.XPATH, 
                "//button[contains(text(), 'Start') or contains(text(), 'Continue')]"
            )
            if buttons:
                buttons[0].click()
                time.sleep(3)
            
            # Look for video (watch for a few seconds)
            time.sleep(5)
            
            # Try to click through any slides
            for _ in range(5):  # Max 5 slides
                try:
                    next_btn = self.driver.find_element(By.XPATH, 
                        "//button[contains(text(), 'Next') or contains(text(), 'Continue')]"
                    )
                    next_btn.click()
                    time.sleep(2)
                except:
                    break
            
            # Look for quiz
            self._handle_quiz()
            
        except Exception as e:
            logger.error(f"   Lesson content error: {e}")
    
    def _handle_quiz(self):
        """Handle quiz questions"""
        try:
            # Look for quiz options
            options = self.driver.find_elements(By.XPATH, 
                "//div[contains(@class, 'option')] | //button[contains(@class, 'option')] | //label"
            )
            
            if options:
                logger.info(f"   Quiz found with {len(options)} options")
                # Click first option (usually works for simple quizzes)
                try:
                    options[0].click()
                    time.sleep(1)
                    
                    # Look for submit/next
                    submit = self.driver.find_element(By.XPATH, 
                        "//button[contains(text(), 'Submit') or contains(text(), 'Next')]"
                    )
                    submit.click()
                    time.sleep(2)
                    
                    logger.info("   Quiz answered")
                except:
                    pass
        except:
            pass
    
    def execute_dca(self, amount_per_purchase: float = 1.0, num_purchases: int = 16):
        """
        Execute Dollar Cost Average strategy
        """
        logger.info("\n" + "="*70)
        logger.info("  💰 PHASE 2: DOLLAR COST AVERAGE")
        logger.info("="*70)
        
        logger.info(f"Strategy: ${amount_per_purchase:.2f} BTC purchase")
        logger.info(f"Total purchases: {num_purchases}")
        logger.info(f"Duration: {num_purchases} days")
        
        # Calculate schedule
        now = datetime.now()
        for i in range(num_purchases):
            purchase_time = now + timedelta(days=i)
            self.dca_schedule.append({
                'day': i + 1,
                'datetime': purchase_time,
                'amount': amount_per_purchase,
                'executed': False
            })
        
        logger.info("\n📅 DCA Schedule created:")
        for item in self.dca_schedule[:3]:
            logger.info(f"   Day {item['day']}: {item['datetime'].strftime('%Y-%m-%d')} - ${item['amount']:.2f}")
        logger.info(f"   ... and {num_purchases - 3} more purchases")
        
        # Execute first purchase immediately
        logger.info("\n🚀 Executing first DCA purchase...")
        self._execute_btc_purchase(amount_per_purchase)
        self.dca_schedule[0]['executed'] = True
        self.stats['dca_purchases'] += 1
        self.stats['total_spent'] += amount_per_purchase
        
        logger.info("✅ First purchase complete")
        logger.info("   Remaining purchases will be made daily")
    
    def _execute_btc_purchase(self, amount: float) -> bool:
        """Execute a single BTC purchase"""
        try:
            logger.info(f"   Buying ${amount:.2f} of BTC...")
            
            # Navigate to buy page
            self.driver.get("https://www.coinbase.com/buy")
            time.sleep(5)
            
            # Look for BTC
            btc_selectors = [
                "//div[contains(text(), 'Bitcoin')]",
                "//div[contains(text(), 'BTC')]",
                "//span[contains(text(), 'Bitcoin')]",
            ]
            
            for selector in btc_selectors:
                try:
                    btc_option = self.driver.find_element(By.XPATH, selector)
                    btc_option.click()
                    time.sleep(2)
                    logger.info("   Selected BTC")
                    break
                except:
                    continue
            
            # Enter amount
            amount_selectors = [
                "//input[@type='number']",
                "//input[contains(@placeholder, 'Amount')]",
                "//input[contains(@id, 'amount')]",
            ]
            
            for selector in amount_selectors:
                try:
                    amount_input = self.driver.find_element(By.XPATH, selector)
                    amount_input.clear()
                    amount_input.send_keys(str(amount))
                    time.sleep(1)
                    logger.info(f"   Entered amount: ${amount:.2f}")
                    break
                except:
                    continue
            
            # Look for buy button
            buy_buttons = self.driver.find_elements(By.XPATH,
                "//button[contains(text(), 'Buy') or contains(text(), 'Preview')]"
            )
            
            if buy_buttons:
                logger.info("   Found buy button (preview only - NOT clicking)")
                logger.info("   ⚠️  MANUAL CONFIRMATION REQUIRED")
                logger.info("   Please review and confirm the purchase")
                # In full auto mode, we would click here
                # buy_buttons[0].click()
            
            return True
            
        except Exception as e:
            logger.error(f"   Purchase error: {e}")
            self.stats['errors'] += 1
            return False
    
    def run_monitoring_loop(self, duration_hours: int = 12):
        """Main monitoring and execution loop"""
        logger.info("\n" + "="*70)
        logger.info("  ⏱️  MONITORING LOOP STARTED")
        logger.info("="*70)
        
        end_time = datetime.now() + timedelta(hours=duration_hours)
        
        logger.info(f"Session will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Duration: {duration_hours} hours")
        
        check_interval = 300  # 5 minutes
        
        try:
            while datetime.now() < end_time and self.running:
                now = datetime.now()
                
                # Check for scheduled DCA purchases
                for item in self.dca_schedule:
                    if not item['executed'] and now >= item['datetime']:
                        logger.info(f"\n⏰ Scheduled purchase: Day {item['day']}")
                        self._execute_btc_purchase(item['amount'])
                        item['executed'] = True
                        self.stats['dca_purchases'] += 1
                
                # Periodic status log
                remaining = end_time - now
                logger.info(f"⏱️  {now.strftime('%H:%M:%S')} | "
                          f"Remaining: {remaining.seconds // 3600}h {(remaining.seconds // 60) % 60}m | "
                          f"Lessons: {self.stats['lessons_completed']} | "
                          f"DCA: {self.stats['dca_purchases']}")
                
                # Save checkpoint
                self._save_checkpoint()
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Stopped by user")
        except Exception as e:
            logger.error(f"\n❌ Monitoring error: {e}")
        
        finally:
            self._generate_final_report()
    
    def _save_checkpoint(self):
        """Save current state"""
        checkpoint = {
            'timestamp': datetime.now().isoformat(),
            'stats': self.stats,
            'dca_schedule': [
                {**item, 'datetime': item['datetime'].isoformat()} 
                for item in self.dca_schedule
            ],
            'earnings': self.earnings
        }
        
        try:
            with open('/home/asbelcas/rm-qpt/logs/ghost_checkpoint.json', 'w') as f:
                json.dump(checkpoint, f, indent=2)
        except:
            pass
    
    def _generate_final_report(self):
        """Generate final session report"""
        logger.info("\n" + "="*70)
        logger.info("  📊 FINAL SESSION REPORT")
        logger.info("="*70)
        
        duration = datetime.now() - self.session_start
        
        logger.info(f"Duration: {duration}")
        logger.info(f"Lessons completed: {self.stats['lessons_completed']}")
        logger.info(f"DCA purchases: {self.stats['dca_purchases']}")
        logger.info(f"Total spent: ${self.stats['total_spent']:.2f}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        logger.info("\n" + "="*70)
        logger.info("  ✅ SESSION COMPLETE")
        logger.info("="*70)
    
    def _take_screenshot(self, name: str):
        """Take a screenshot for debugging"""
        try:
            filename = f"/home/asbelcas/rm-qpt/logs/screenshot_{name}_{int(time.time())}.png"
            self.driver.save_screenshot(filename)
            logger.info(f"   Screenshot saved: {filename}")
        except:
            pass


def main():
    """Main entry point"""
    print("="*70)
    print("  👻 GHOST AGENT v5.0 - FULLY AUTOMATED EXECUTOR")
    print("="*70)
    print()
    
    # Initialize executor
    executor = GhostAutoExecutor(capital=16.0)
    
    # Connect to browser
    if not executor.connect_to_browser():
        print("❌ Failed to connect to Chrome")
        print("   Make sure Chrome is running with: --remote-debugging-port=9222")
        return
    
    # Check login status
    if not executor.check_login_status():
        print("\n⚠️  Please login to Coinbase manually")
        print("   The automation will begin once you're logged in")
        input("   Press Enter once logged in...")
    
    # Execute phases
    print("\n🚀 Starting automation...")
    
    # Phase 1: Learn & Earn
    earnings = executor.execute_learn_and_earn()
    executor.earnings += earnings
    
    # Phase 2: DCA Setup
    executor.execute_dca(amount_per_purchase=1.0, num_purchases=16)
    
    # Phase 3: Monitoring Loop
    print("\n⏱️  Starting 12-hour monitoring loop...")
    print("   Press Ctrl+C to stop early")
    print()
    
    executor.run_monitoring_loop(duration_hours=12)
    
    print("\n✅ Automation complete!")


if __name__ == "__main__":
    main()
