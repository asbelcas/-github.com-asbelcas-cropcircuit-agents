#!/usr/bin/env python3
"""
RM-QPT ROBUST GHOST AGENT v5.0
Production-hardened with comprehensive failure handling
"""

import os
import sys
import json
import time
import random
import subprocess
import platform
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import hashlib
import pickle

# Selenium imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, WebDriverException,
        SessionNotCreatedException, ElementNotInteractableException
    )
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# Optional imports
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# ============================================================================
# CONFIGURATION & CONSTANTS
# ============================================================================

class Config:
    """System configuration"""
    # Session settings
    SESSION_DURATION_HOURS = 12
    CHECKPOINT_INTERVAL_MINUTES = 30
    MAX_RETRY_ATTEMPTS = 3
    
    # Safety limits
    MAX_TRANSACTION_USD = 50.0
    RATE_LIMIT_BASE_DELAY = 60  # seconds
    
    # Monitoring
    HEALTH_CHECK_INTERVAL = 30  # seconds
    RESOURCE_CHECK_INTERVAL = 300  # 5 minutes
    
    # File paths
    CHECKPOINT_DIR = "checkpoints"
    LOG_DIR = "logs"
    SCREENSHOT_DIR = "screenshots"
    
    # URLs
    COINBASE_URL = "https://www.coinbase.com"
    COINBASE_PORTFOLIO = "https://www.coinbase.com/portfolio"
    COINBASE_LEARN = "https://www.coinbase.com/learn"


# ============================================================================
# FAILURE HANDLING CLASSES
# ============================================================================

class BrowserHealthMonitor:
    """Monitor and recover browser health"""
    
    def __init__(self, driver=None):
        self.driver = driver
        self.last_health_check = time.time()
        self.health_check_interval = Config.HEALTH_CHECK_INTERVAL
        self.consecutive_failures = 0
        self.max_failures = 3
    
    def set_driver(self, driver):
        self.driver = driver
    
    def is_browser_alive(self) -> Tuple[bool, str]:
        """Check if browser is responsive"""
        if not self.driver:
            return False, "No driver"
        
        try:
            # Lightweight check
            _ = self.driver.current_url
            self.consecutive_failures = 0
            return True, "Healthy"
        except Exception as e:
            self.consecutive_failures += 1
            return False, str(e)
    
    def check_health(self) -> bool:
        """Periodic health check"""
        if time.time() - self.last_health_check < self.health_check_interval:
            return True
        
        self.last_health_check = time.time()
        is_alive, message = self.is_browser_alive()
        
        if not is_alive:
            print(f"⚠️ Browser health check failed: {message}")
            print(f"   Consecutive failures: {self.consecutive_failures}")
        
        return is_alive
    
    def needs_recovery(self) -> bool:
        """Check if recovery is needed"""
        return self.consecutive_failures >= self.max_failures


class NetworkMonitor:
    """Monitor network connectivity"""
    
    def __init__(self):
        self.last_check = 0
        self.check_interval = 60
        self.is_available = True
    
    def is_connected(self) -> bool:
        """Check internet connectivity"""
        if time.time() - self.last_check < self.check_interval:
            return self.is_available
        
        self.last_check = time.time()
        
        if not REQUESTS_AVAILABLE:
            # Fallback: assume connected
            return True
        
        try:
            response = requests.get(
                "https://www.coinbase.com",
                timeout=5,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            self.is_available = response.status_code == 200
            return self.is_available
        except:
            self.is_available = False
            return False
    
    def wait_for_connection(self, timeout: int = 300) -> bool:
        """Wait for connection to return"""
        print("🌐 Waiting for internet connection...")
        start = time.time()
        
        while time.time() - start < timeout:
            if self.is_connected():
                print("✅ Connection restored")
                return True
            
            remaining = int(timeout - (time.time() - start))
            print(f"   Waiting... ({remaining}s remaining)")
            time.sleep(10)
        
        print("❌ Connection timeout")
        return False


class SessionManager:
    """Manage browser session persistence"""
    
    def __init__(self, driver=None):
        self.driver = driver
        self.session_start = time.time()
        self.last_activity = time.time()
        self.session_valid = False
        self.cookie_backup = None
    
    def set_driver(self, driver):
        self.driver = driver
    
    def validate_session(self) -> Tuple[bool, str]:
        """Check if Coinbase session is still valid"""
        if not self.driver:
            return False, "No driver"
        
        try:
            # Navigate to portfolio
            current_url = self.driver.current_url
            
            # Check if redirected to login
            if "/signin" in current_url:
                return False, "Redirected to login"
            
            # Check for logged-in indicators
            page_source = self.driver.page_source.lower()
            
            logged_in_indicators = [
                "portfolio",
                "balances",
                "trade",
                "send",
                "receive",
            ]
            
            for indicator in logged_in_indicators:
                if indicator in page_source:
                    self.last_activity = time.time()
                    return True, "Session valid"
            
            return False, "Unknown state"
            
        except Exception as e:
            return False, f"Error: {e}"
    
    def backup_cookies(self):
        """Backup current cookies"""
        try:
            self.cookie_backup = self.driver.get_cookies()
            return True
        except:
            return False
    
    def restore_session(self) -> bool:
        """Attempt to restore session from backup"""
        if not self.cookie_backup:
            return False
        
        try:
            self.driver.get(Config.COINBASE_URL)
            time.sleep(3)
            
            for cookie in self.cookie_backup:
                try:
                    self.driver.add_cookie(cookie)
                except:
                    pass
            
            self.driver.refresh()
            time.sleep(3)
            
            is_valid, _ = self.validate_session()
            return is_valid
            
        except Exception as e:
            print(f"Session restore failed: {e}")
            return False


class RateLimitHandler:
    """Handle rate limiting with exponential backoff"""
    
    def __init__(self):
        self.attempts = 0
        self.base_delay = Config.RATE_LIMIT_BASE_DELAY
        self.max_delay = 3600
    
    def handle_rate_limit(self):
        """Wait with exponential backoff"""
        self.attempts += 1
        delay = min(self.base_delay * (2 ** (self.attempts - 1)), self.max_delay)
        
        print(f"⏳ Rate limited. Waiting {delay} seconds...")
        
        # Wait with progress updates
        for i in range(0, delay, 30):
            remaining = delay - i
            print(f"   {remaining}s remaining...")
            time.sleep(min(30, remaining))
        
        print("   Resuming...")
    
    def reset(self):
        if self.attempts > 0:
            print("✅ Rate limit cleared")
            self.attempts = 0


class CheckpointManager:
    """Manage session checkpoints for recovery"""
    
    def __init__(self):
        os.makedirs(Config.CHECKPOINT_DIR, exist_ok=True)
        self.checkpoint_file = None
    
    def set_session_id(self, session_id: str):
        self.checkpoint_file = os.path.join(
            Config.CHECKPOINT_DIR,
            f"checkpoint_{session_id}.json"
        )
    
    def save_checkpoint(self, data: Dict):
        """Save current session state"""
        if not self.checkpoint_file:
            return False
        
        try:
            checkpoint = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Checkpoint save failed: {e}")
            return False
    
    def load_checkpoint(self) -> Optional[Dict]:
        """Load last checkpoint"""
        if not self.checkpoint_file or not os.path.exists(self.checkpoint_file):
            return None
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
            
            print(f"📂 Loaded checkpoint from {checkpoint['timestamp']}")
            return checkpoint.get('data')
        except Exception as e:
            print(f"Checkpoint load failed: {e}")
            return None
    
    def list_checkpoints(self) -> List[str]:
        """List all available checkpoints"""
        try:
            files = os.listdir(Config.CHECKPOINT_DIR)
            return [f for f in files if f.startswith('checkpoint_')]
        except:
            return []


class SystemResourceMonitor:
    """Monitor system resources"""
    
    def __init__(self):
        self.last_check = 0
        self.check_interval = Config.RESOURCE_CHECK_INTERVAL
    
    def check_resources(self) -> Tuple[bool, str]:
        """Check if system has sufficient resources"""
        if time.time() - self.last_check < self.check_interval:
            return True, "OK"
        
        self.last_check = time.time()
        
        if not PSUTIL_AVAILABLE:
            return True, "psutil not available"
        
        # Check memory
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            return False, f"High memory usage: {memory.percent}%"
        
        # Check disk
        disk = psutil.disk_usage('/')
        if disk.percent > 95:
            return False, f"Low disk space: {disk.percent}%"
        
        # Check CPU (optional)
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 95:
            return False, f"High CPU usage: {cpu_percent}%"
        
        return True, f"Memory: {memory.percent}%, Disk: {disk.percent}%"
    
    def prevent_sleep(self):
        """Prevent computer from sleeping"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            try:
                subprocess.Popen(['caffeinate', '-d', '-i', '-s'])
                print("☕ Preventing sleep (macOS caffeinate)")
            except:
                print("⚠️ Could not prevent sleep on macOS")
        
        elif system == "Linux":
            try:
                subprocess.Popen([
                    'systemd-inhibit',
                    '--what=idle:sleep:handle-lid-switch',
                    '--why=Coinbase Ghost Agent',
                    '--mode=block',
                    'sleep', 'infinity'
                ])
                print("☕ Preventing sleep (Linux)")
            except:
                print("⚠️ Could not prevent sleep on Linux")
        
        elif system == "Windows":
            try:
                import ctypes
                ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
                print("☕ Preventing sleep (Windows)")
            except:
                print("⚠️ Could not prevent sleep on Windows")


class RobustElementFinder:
    """Find elements with multiple fallback strategies"""
    
    def __init__(self, driver):
        self.driver = driver
        self.success_history = {}
    
    def find_element(self, identifier: str, element_type: str = "button", 
                     max_wait: int = 10) -> Optional[Any]:
        """Find element using multiple strategies"""
        
        strategies = self._build_strategies(identifier, element_type)
        
        # Try cached successful strategy first
        cache_key = f"{element_type}:{identifier}"
        if cache_key in self.success_history:
            strategy = self.success_history[cache_key]
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(strategy)
                )
                return element
            except:
                pass  # Fall through to other strategies
        
        # Try all strategies
        for strategy in strategies:
            try:
                element = WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located(strategy)
                )
                
                # Cache successful strategy
                self.success_history[cache_key] = strategy
                
                return element
            except:
                continue
        
        # Last resort: fuzzy text search
        try:
            elements = self.driver.find_elements(
                By.XPATH, 
                f"//*[contains(text(), '{identifier}')]"
            )
            if elements:
                return elements[0]
        except:
            pass
        
        return None
    
    def _build_strategies(self, identifier: str, element_type: str) -> List[Tuple]:
        """Build list of finder strategies"""
        strategies = []
        
        if element_type == "button":
            strategies = [
                (By.XPATH, f"//button[contains(text(), '{identifier}')]"),
                (By.XPATH, f"//button[@aria-label='{identifier}']"),
                (By.CSS_SELECTOR, f"button[data-testid*='{identifier}']"),
                (By.CSS_SELECTOR, f"button[class*='{identifier}']"),
                (By.XPATH, f"//*[@role='button' and contains(text(), '{identifier}')]"),
            ]
        elif element_type == "input":
            strategies = [
                (By.ID, identifier),
                (By.NAME, identifier),
                (By.XPATH, f"//input[@placeholder='{identifier}']"),
                (By.XPATH, f"//input[@aria-label='{identifier}']"),
                (By.CSS_SELECTOR, f"input[type='{identifier}']"),
            ]
        elif element_type == "link":
            strategies = [
                (By.LINK_TEXT, identifier),
                (By.PARTIAL_LINK_TEXT, identifier),
                (By.XPATH, f"//a[contains(text(), '{identifier}')]"),
            ]
        
        return strategies


# ============================================================================
# MAIN ROBUST AGENT CLASS
# ============================================================================

class RobustGhostAgent:
    """
    Production-hardened Ghost Agent with comprehensive failure handling
    INTEGRATED: Crypto Trading Knowledge Base v5.0
    """
    
    def __init__(self, capital: float = 16.0):
        self.driver = None
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:12]
        self.capital = capital
        
        # Initialize monitoring components
        self.browser_monitor = BrowserHealthMonitor()
        self.network_monitor = NetworkMonitor()
        self.session_manager = SessionManager()
        self.rate_limit_handler = RateLimitHandler()
        self.checkpoint_manager = CheckpointManager()
        self.resource_monitor = SystemResourceMonitor()
        self.element_finder = None
        
        self.checkpoint_manager.set_session_id(self.session_id)
        
        # Session state
        self.earnings = 0.0
        self.actions_completed = 0
        self.opportunities = []
        self.session_start_time = None
        self.emergency_stop = False
        self.current_positions = []
        self.daily_trades = 0
        self.daily_pnl = 0.0
        
        # Initialize trading knowledge base
        self._init_trading_knowledge()
        
        # Create directories
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
        
        print(f"🤖 Robust Ghost Agent initialized")
        print(f"   Session ID: {self.session_id}")
        print(f"   Capital: ${self.capital:.2f}")
    
    def _init_trading_knowledge(self):
        """Initialize trading knowledge base"""
        try:
            # Import trading knowledge
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from core.trading_knowledge_integration import TradingKnowledgeIntegrator
            
            self.trading_kb = TradingKnowledgeIntegrator(capital=self.capital)
            self.trading_enabled = True
            
            print(f"🧠 Trading Knowledge Base loaded")
            print(f"   Strategies: {len(self.trading_kb.kb.strategies)}")
            print(f"   Risk Rules: {len(self.trading_kb.kb.risk_management['stop_loss_rules'])}")
            
            # Print daily briefing
            print("\n" + self.trading_kb.generate_daily_briefing())
            
        except Exception as e:
            print(f"⚠️ Trading knowledge not loaded: {e}")
            self.trading_kb = None
            self.trading_enabled = False
    
    def check_prerequisites(self) -> Tuple[bool, str]:
        """Check if system is ready to run"""
        
        # Check Selenium
        if not SELENIUM_AVAILABLE:
            return False, "Selenium not installed. Run: pip install selenium webdriver-manager"
        
        # Check Chrome
        chrome_ok, chrome_msg = self._check_chrome()
        if not chrome_ok:
            return False, f"Chrome not found: {chrome_msg}"
        
        # Check resources
        resources_ok, resources_msg = self.resource_monitor.check_resources()
        if not resources_ok:
            return False, f"Insufficient resources: {resources_msg}"
        
        return True, "All checks passed"
    
    def _check_chrome(self) -> Tuple[bool, str]:
        """Check if Chrome is installed"""
        try:
            result = subprocess.run(
                ['google-chrome', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, result.stdout.strip()
        except:
            pass
        
        # Check common paths
        paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ]
        
        for path in paths:
            if os.path.exists(path):
                return True, f"Found at {path}"
        
        return False, "Chrome not found in standard locations"
    
    def initialize_driver(self) -> bool:
        """Initialize browser with fallback strategies"""
        
        print("\n🌐 Initializing browser...")
        
        methods = [
            self._init_with_manager,
            self._init_system_chromedriver,
            self._init_firefox_fallback,
        ]
        
        for i, method in enumerate(methods, 1):
            try:
                print(f"   Trying method {i}...")
                driver = method()
                if driver:
                    self.driver = driver
                    self.browser_monitor.set_driver(driver)
                    self.session_manager.set_driver(driver)
                    self.element_finder = RobustElementFinder(driver)
                    
                    print(f"   ✅ Browser initialized (method {i})")
                    return True
            except Exception as e:
                print(f"   ⚠️ Method {i} failed: {str(e)[:50]}")
                continue
        
        print("❌ All browser initialization methods failed")
        return False
    
    def _init_with_manager(self):
        """Initialize with webdriver-manager"""
        from webdriver_manager.chrome import ChromeDriverManager
        
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        return driver
    
    def _init_system_chromedriver(self):
        """Initialize with system chromedriver"""
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        return driver
    
    def _init_firefox_fallback(self):
        """Fallback to Firefox"""
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        
        options = FirefoxOptions()
        options.add_argument("--no-sandbox")
        
        driver = webdriver.Firefox(options=options)
        return driver
    
    def execute_with_protection(self, task_func: Callable, *args, **kwargs) -> Any:
        """Execute task with full error protection"""
        
        max_retries = Config.MAX_RETRY_ATTEMPTS
        attempt = 0
        
        while attempt < max_retries:
            try:
                # Pre-execution checks
                if not self.network_monitor.is_connected():
                    if not self.network_monitor.wait_for_connection():
                        raise Exception("Network unavailable")
                
                resources_ok, resources_msg = self.resource_monitor.check_resources()
                if not resources_ok:
                    print(f"⚠️ Resource warning: {resources_msg}")
                    time.sleep(30)  # Wait and retry
                    attempt += 1
                    continue
                
                # Check browser health
                if not self.browser_monitor.check_health():
                    if self.browser_monitor.needs_recovery():
                        print("🔄 Attempting browser recovery...")
                        self._recover_browser()
                
                # Execute task
                result = task_func(*args, **kwargs)
                
                # Post-execution
                self.rate_limit_handler.reset()
                self.save_checkpoint()
                
                return result
                
            except Exception as e:
                attempt += 1
                error_msg = str(e).lower()
                
                print(f"⚠️ Error on attempt {attempt}: {str(e)[:80]}")
                
                # Handle specific errors
                if "rate limit" in error_msg or "429" in error_msg:
                    self.rate_limit_handler.handle_rate_limit()
                    continue
                
                if "timeout" in error_msg:
                    time.sleep(30)
                    continue
                
                if "no such element" in error_msg:
                    # Element not found - might be UI change
                    time.sleep(5)
                    continue
                
                if attempt >= max_retries:
                    print("❌ Max retries reached")
                    self.save_emergency_checkpoint()
                    raise
                
                time.sleep(10)
        
        return None
    
    def _recover_browser(self):
        """Attempt to recover browser session"""
        try:
            # Try to save cookies
            self.session_manager.backup_cookies()
            
            # Quit old driver
            try:
                self.driver.quit()
            except:
                pass
            
            # Reinitialize
            if self.initialize_driver():
                # Try to restore session
                if self.session_manager.restore_session():
                    print("✅ Browser and session recovered")
                    return True
            
            return False
            
        except Exception as e:
            print(f"Browser recovery failed: {e}")
            return False
    
    def save_checkpoint(self):
        """Save current session state"""
        data = {
            'earnings': self.earnings,
            'actions_completed': self.actions_completed,
            'opportunities': [asdict(o) if hasattr(o, '__dataclass_fields__') else o 
                            for o in self.opportunities],
            'session_start': self.session_start_time.isoformat() if self.session_start_time else None,
        }
        
        self.checkpoint_manager.save_checkpoint(data)
    
    def save_emergency_checkpoint(self):
        """Save emergency state on failure"""
        emergency_data = {
            'timestamp': datetime.now().isoformat(),
            'earnings': self.earnings,
            'actions_completed': self.actions_completed,
            'error_state': True,
        }
        
        filename = f"emergency_{self.session_id}_{int(time.time())}.json"
        filepath = os.path.join(Config.CHECKPOINT_DIR, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(emergency_data, f, indent=2)
            print(f"💾 Emergency checkpoint saved: {filename}")
        except Exception as e:
            print(f"Failed to save emergency checkpoint: {e}")
    
    def detect_blocking_issues(self) -> Tuple[bool, str]:
        """Detect if blocked by CAPTCHA, security, etc."""
        
        if not self.driver:
            return False, "No driver"
        
        page_source = self.driver.page_source.lower()
        
        # Check for CAPTCHA
        captcha_indicators = ["captcha", "i'm not a robot", "recaptcha", "verify you are human"]
        for indicator in captcha_indicators:
            if indicator in page_source:
                return True, f"CAPTCHA detected: {indicator}"
        
        # Check for security prompts
        security_indicators = ["verify it's you", "confirm your identity", "security check", "unusual activity"]
        for indicator in security_indicators:
            if indicator in page_source:
                return True, f"Security prompt: {indicator}"
        
        # Check for account issues
        account_indicators = ["account locked", "account restricted", "access denied"]
        for indicator in account_indicators:
            if indicator in page_source:
                return True, f"Account issue: {indicator}"
        
        # Check for rate limiting
        if "rate limit" in page_source or "too many requests" in page_source:
            return True, "Rate limited"
        
        return False, "No blocking issues"
    
    def run_protected_session(self, duration_hours: int = None):
        """Run a fully protected session"""
        
        if duration_hours is None:
            duration_hours = Config.SESSION_DURATION_HOURS
        
        # Check prerequisites
        prereq_ok, prereq_msg = self.check_prerequisites()
        if not prereq_ok:
            print(f"❌ Prerequisites not met: {prereq_msg}")
            return False
        
        # Initialize browser
        if not self.initialize_driver():
            print("❌ Failed to initialize browser")
            return False
        
        # Prevent sleep
        self.resource_monitor.prevent_sleep()
        
        # Set session start
        self.session_start_time = datetime.now()
        session_end = self.session_start_time + timedelta(hours=duration_hours)
        
        print(f"\n🚀 Starting protected {duration_hours}-hour session")
        print(f"   Start: {self.session_start_time.strftime('%H:%M:%S')}")
        print(f"   End: {session_end.strftime('%H:%M:%S')}")
        print(f"   Session ID: {self.session_id}")
        
        # Main execution loop
        try:
            while datetime.now() < session_end and not self.emergency_stop:
                # Periodic checkpoint
                if (datetime.now() - self.session_start_time).seconds % (Config.CHECKPOINT_INTERVAL_MINUTES * 60) < 60:
                    self.save_checkpoint()
                
                # Check for blocking issues
                is_blocked, block_reason = self.detect_blocking_issues()
                if is_blocked:
                    print(f"\n🚨 BLOCKING ISSUE: {block_reason}")
                    self.handle_blocking_issue(block_reason)
                    continue
                
                # Health checks
                if not self.browser_monitor.check_health():
                    if not self._recover_browser():
                        print("❌ Cannot recover browser, stopping")
                        break
                
                # Session validation
                is_valid, session_msg = self.session_manager.validate_session()
                if not is_valid:
                    print(f"⚠️ Session invalid: {session_msg}")
                    if not self.session_manager.restore_session():
                        print("❌ Cannot restore session")
                        break
                
                # Main work would go here
                # For now, just sleep and monitor
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            self.save_emergency_checkpoint()
        finally:
            self.shutdown()
        
        return True
    
    def handle_blocking_issue(self, reason: str):
        """Handle blocking issues like CAPTCHA"""
        print(f"   Taking screenshot...")
        
        try:
            screenshot_path = os.path.join(
                Config.SCREENSHOT_DIR,
                f"blocking_issue_{int(time.time())}.png"
            )
            self.driver.save_screenshot(screenshot_path)
            print(f"   Screenshot saved: {screenshot_path}")
        except:
            pass
        
        print(f"   ⚠️ Manual intervention required")
        print(f"   Reason: {reason}")
        print(f"   Please resolve the issue in the browser window")
        input("   Press Enter after resolving...")
    
    def shutdown(self):
        """Clean shutdown"""
        print("\n🛑 Shutting down...")
        
        self.save_checkpoint()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        print(f"✅ Session ended")
        print(f"   Earnings: ${self.earnings:.2f}")
        print(f"   Actions: {self.actions_completed}")
        print(f"   Checkpoints saved in: {Config.CHECKPOINT_DIR}/")


    def get_trading_decision(self, opportunity: Dict) -> Dict:
        """
        Get intelligent trading decision using knowledge base
        
        Args:
            opportunity: Dict with opportunity details
            
        Returns:
            Trading decision with action, size, stops
        """
        if not self.trading_enabled or not self.trading_kb:
            # Fallback: simple logic
            return {
                'action': 'HOLD',
                'asset': opportunity.get('asset', 'BTC'),
                'amount': 0,
                'reason': 'Trading knowledge not available'
            }
        
        try:
            decision = self.trading_kb.evaluate_opportunity(
                opportunity, self.current_positions
            )
            
            return {
                'action': decision.action,
                'asset': decision.asset,
                'amount': decision.amount,
                'confidence': decision.confidence,
                'reasons': decision.reasons,
                'risk_level': decision.risk_level,
                'entry_price': decision.entry_price,
                'stop_loss': decision.stop_loss,
                'take_profit': decision.take_profit,
                'strategy': decision.strategy
            }
            
        except Exception as e:
            print(f"⚠️ Trading decision error: {e}")
            return {
                'action': 'HOLD',
                'asset': opportunity.get('asset', 'BTC'),
                'amount': 0,
                'reason': f'Error: {e}'
            }
    
    def update_capital(self, new_capital: float):
        """Update capital and re-evaluate strategies"""
        old_capital = self.capital
        self.capital = new_capital
        
        if self.trading_kb:
            self.trading_kb.update_capital(new_capital)
        
        print(f"💰 Capital updated: ${old_capital:.2f} → ${new_capital:.2f}")
    
    def log_trade_result(self, trade: Dict, result: str, pnl: float = 0.0):
        """Log trade result and update stats"""
        self.daily_trades += 1
        self.daily_pnl += pnl
        self.earnings += pnl
        
        if self.trading_kb:
            from core.trading_knowledge_integration import TradingDecision
            decision = TradingDecision(
                action=trade.get('action', 'HOLD'),
                asset=trade.get('asset', 'UNKNOWN'),
                amount=trade.get('amount', 0),
                strategy=trade.get('strategy', 'Unknown'),
                confidence=trade.get('confidence', 0.5),
                reasons=trade.get('reasons', []),
                risk_level=trade.get('risk_level', 5)
            )
            self.trading_kb.log_trade(decision, result)
        
        print(f"📝 Trade logged: {result} | P&L: ${pnl:+.2f}")


def main():
    """Main entry point"""
    print("="*70)
    print("  ROBUST GHOST AGENT v5.0 + TRADING MASTERY")
    print("  Production-hardened with Crypto Trading Knowledge Base")
    print("="*70)
    print()
    
    # Get capital from user or use default
    capital = 16.0
    try:
        user_input = input("Enter starting capital (default $16.00): $").strip()
        if user_input:
            capital = float(user_input)
    except:
        pass
    
    agent = RobustGhostAgent(capital=capital)
    
    # Run protected session
    agent.run_protected_session(duration_hours=12)


if __name__ == "__main__":
    main()
