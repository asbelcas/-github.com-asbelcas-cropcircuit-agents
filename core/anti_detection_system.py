#!/usr/bin/env python3
"""
RM-QPT ANTI-DETECTION SYSTEM v1.0
Proactive countermeasures against automation detection
"""

import os
import json
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import hashlib

class StealthProfile:
    """
    Generates and manages unique browser fingerprints
    Each session gets a different profile
    """
    
    def __init__(self):
        self.profile = self._generate_profile()
        self.mouse_path = []
        self.typing_patterns = self._generate_typing_patterns()
    
    def _generate_profile(self) -> Dict:
        """Generate realistic browser fingerprint"""
        
        # Realistic screen resolutions
        screen_resolutions = [
            (1920, 1080),
            (1366, 768),
            (2560, 1440),
            (1440, 900),
            (1536, 864),
            (1680, 1050),
        ]
        
        # Realistic user agents
        user_agents = [
            # Windows Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
            # macOS Chrome
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            # Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        # Timezone offsets
        timezones = [
            "America/New_York",
            "America/Chicago",
            "America/Denver",
            "America/Los_Angeles",
            "Europe/London",
            "Europe/Paris",
            "Asia/Tokyo",
        ]
        
        # Accept languages
        accept_languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.8",
            "en-CA,en;q=0.9,fr;q=0.8",
        ]
        
        # Canvas noise seed (unique per session)
        canvas_seed = random.randint(1000, 9999)
        
        # WebGL vendor/renderer combinations
        webgl_configs = [
            ("Intel Inc.", "Intel Iris OpenGL Engine"),
            ("NVIDIA Corporation", "NVIDIA GeForce GTX 1050/PCIe/SSE2"),
            ("Apple Inc.", "Apple M1"),
            ("Google Inc.", "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"),
        ]
        
        # Font lists (varies by OS)
        font_lists = {
            "Windows": "Arial, Calibri, Cambria, Consolas, Courier New, Georgia, Segoe UI, Tahoma, Times New Roman, Verdana",
            "Mac": "Arial, Courier, Georgia, Helvetica, Monaco, Times, Verdana, -apple-system, BlinkMacSystemFont",
            "Linux": "DejaVu Sans, Liberation Sans, Noto Sans, Ubuntu, Arial, Helvetica",
        }
        
        # Pick a platform
        platform = random.choice(["Windows", "Mac", "Linux"])
        webgl_vendor, webgl_renderer = random.choice(webgl_configs)
        
        return {
            "session_id": hashlib.md5(str(time.time()).encode()).hexdigest()[:12],
            "created_at": datetime.now().isoformat(),
            "user_agent": random.choice(user_agents),
            "screen_resolution": random.choice(screen_resolutions),
            "viewport": self._calculate_viewport(random.choice(screen_resolutions)),
            "timezone": random.choice(timezones),
            "timezone_offset": self._get_timezone_offset(random.choice(timezones)),
            "accept_language": random.choice(accept_languages),
            "platform": platform,
            "canvas_seed": canvas_seed,
            "webgl_vendor": webgl_vendor,
            "webgl_renderer": webgl_renderer,
            "fonts": font_lists.get(platform, font_lists["Windows"]),
            "color_depth": random.choice([24, 32]),
            "pixel_ratio": random.choice([1, 1.25, 1.5, 2]),
            "touch_support": random.choice([True, False]),
            "hardware_concurrency": random.choice([4, 6, 8, 12, 16]),
            "device_memory": random.choice([4, 8, 16, 32]),
            "max_touch_points": random.choice([0, 5, 10]),
        }
    
    def _calculate_viewport(self, resolution: Tuple[int, int]) -> Tuple[int, int]:
        """Calculate realistic viewport (slightly smaller than screen)"""
        width, height = resolution
        # Account for browser chrome, taskbar, etc.
        viewport_width = width - random.randint(20, 100)
        viewport_height = height - random.randint(100, 200)
        return (viewport_width, viewport_height)
    
    def _get_timezone_offset(self, timezone: str) -> int:
        """Get timezone offset in minutes"""
        offsets = {
            "America/New_York": -300,
            "America/Chicago": -360,
            "America/Denver": -420,
            "America/Los_Angeles": -480,
            "Europe/London": 0,
            "Europe/Paris": 60,
            "Asia/Tokyo": 540,
        }
        return offsets.get(timezone, -300)
    
    def _generate_typing_patterns(self) -> Dict:
        """Generate human-like typing patterns"""
        return {
            "wpm_range": (30, 70),  # Words per minute
            "error_rate": (0.02, 0.08),  # 2-8% error rate
            "pause_after_word": (0.3, 1.2),  # Pause after words
            "pause_after_sentence": (1.0, 3.0),
            "backspace_delay": (0.1, 0.3),
        }
    
    def get_selenium_options(self):
        """Generate Selenium ChromeOptions with stealth settings"""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        
        # Basic stealth
        options.add_argument(f"--user-agent={self.profile['user_agent']}")
        options.add_argument(f"--window-size={self.profile['viewport'][0]},{self.profile['viewport'][1]}")
        options.add_argument("--start-maximized")
        
        # Anti-detection arguments
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Fingerprint randomization
        options.add_argument(f"--force-device-scale-factor={self.profile['pixel_ratio']}")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-images")  # Optional: faster loading
        
        # Experimental options
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        })
        
        return options
    
    def get_stealth_js(self) -> str:
        """Generate JavaScript to inject for anti-detection"""
        
        js = f"""
        // Override navigator.webdriver
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined
        }});
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [1, 2, 3, 4, 5]
        }});
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{self.profile['accept_language'].split(',')[0]}', 'en-US', 'en']
        }});
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{self.profile['platform']}'
        }});
        
        // Override hardwareConcurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {self.profile['hardware_concurrency']}
        }});
        
        // Override deviceMemory
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {self.profile['device_memory']}
        }});
        
        // Canvas fingerprint randomization
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            if (type === 'image/png' && this.width > 0 && this.height > 0) {{
                // Add subtle noise to canvas
                const ctx = this.getContext('2d');
                const imageData = ctx.getImageData(0, 0, this.width, this.height);
                const data = imageData.data;
                // Modify pixel data slightly
                for (let i = 0; i < data.length; i += 4) {{
                    if (Math.random() > 0.999) {{
                        data[i] = Math.max(0, Math.min(255, data[i] + Math.random() > 0.5 ? 1 : -1));
                    }}
                }}
                ctx.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
        
        // WebGL fingerprint randomization
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{
                return '{self.profile['webgl_vendor']}';
            }}
            if (parameter === 37446) {{
                return '{self.profile['webgl_renderer']}';
            }}
            return getParameter(parameter);
        }};
        
        // Hide Selenium marks
        const keysToRemove = [
            '__webdriver_script_fn',
            '__webdriver_evaluate',
            '__selenium_evaluate',
            '__fxdriver_evaluate',
            '_phantom',
            '__webdriver__',
            'callPhantom',
            '_selenium',
            'callSelenium',
            '__nightmare__'
        ];
        
        keysToRemove.forEach(key => {{
            if (window[key]) window[key] = undefined;
        }});
        
        console.log = function(){{}};  // Disable console logging
        """
        
        return js


class HumanBehaviorSimulator:
    """
    Simulates realistic human behavior patterns
    """
    
    def __init__(self, profile: StealthProfile):
        self.profile = profile
        self.last_mouse_pos = (0, 0)
        self.typing_wpm = random.randint(
            profile.typing_patterns['wpm_range'][0],
            profile.typing_patterns['wpm_range'][1]
        )
        self.char_delay = 60.0 / (self.typing_wpm * 5)  # Average word is 5 chars
    
    def human_like_delay(self, action_type: str = "general"):
        """Generate human-like delays between actions"""
        
        delays = {
            "page_load": (3, 8),
            "element_find": (0.5, 2),
            "click": (0.3, 1.5),
            "typing": (self.char_delay * 0.5, self.char_delay * 1.5),
            "read": (10, 30),  # Time to "read" content
            "scroll": (0.5, 3),
            "form_submit": (2, 5),
        }
        
        min_delay, max_delay = delays.get(action_type, (1, 3))
        
        # Add some randomness with occasional longer pauses
        if random.random() < 0.05:  # 5% chance of longer pause
            max_delay *= 2
        
        time.sleep(random.uniform(min_delay, max_delay))
    
    def human_like_mouse_move(self, driver, target_element):
        """
        Move mouse to element with human-like curve
        Uses bezier curve for natural movement
        """
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            
            # Get current and target positions
            current_x, current_y = self.last_mouse_pos
            
            # Get target element location
            location = target_element.location
            size = target_element.size
            target_x = location['x'] + size['width'] / 2 + random.randint(-10, 10)
            target_y = location['y'] + size['height'] / 2 + random.randint(-10, 10)
            
            # Generate intermediate points for bezier curve
            num_points = random.randint(3, 7)
            points = []
            
            for i in range(num_points):
                t = (i + 1) / (num_points + 1)
                # Add randomness for curve
                offset_x = random.randint(-50, 50)
                offset_y = random.randint(-50, 50)
                
                x = current_x + (target_x - current_x) * t + offset_x
                y = current_y + (target_y - current_y) * t + offset_y
                points.append((x, y))
            
            # Move through points
            actions = ActionChains(driver)
            for x, y in points:
                actions.move_by_offset(x - current_x, y - current_y)
                actions.pause(random.uniform(0.05, 0.2))
                current_x, current_y = x, y
            
            actions.perform()
            self.last_mouse_pos = (target_x, target_y)
            
        except Exception as e:
            # Fallback to simple click
            pass
    
    def human_like_typing(self, element, text: str):
        """
        Type text with human-like patterns including occasional errors
        """
        error_rate = random.uniform(
            self.profile.typing_patterns['error_rate'][0],
            self.profile.typing_patterns['error_rate'][1]
        )
        
        for char in text:
            # Occasional typo
            if random.random() < error_rate and char.isalpha():
                # Type wrong character
                wrong_char = random.choice(string.ascii_lowercase)
                element.send_keys(wrong_char)
                time.sleep(random.uniform(0.1, 0.3))
                
                # Backspace
                element.send_keys('\b')
                time.sleep(random.uniform(0.1, 0.3))
            
            # Type correct character
            element.send_keys(char)
            
            # Variable delay between keystrokes
            delay = random.uniform(
                self.profile.typing_patterns['typing'][0],
                self.profile.typing_patterns['typing'][1]
            )
            
            # Slower after spaces (thinking time)
            if char == ' ':
                delay += random.uniform(
                    self.profile.typing_patterns['pause_after_word'][0],
                    self.profile.typing_patterns['pause_after_word'][1]
                )
            
            time.sleep(delay)
    
    def simulate_reading(self, duration: int = None):
        """Simulate reading page content"""
        if duration is None:
            duration = random.randint(10, 30)
        time.sleep(duration)
    
    def random_scroll(self, driver):
        """Random scroll behavior"""
        scroll_amount = random.randint(100, 500)
        direction = random.choice([-1, 1])
        
        driver.execute_script(f"window.scrollBy(0, {scroll_amount * direction});")
        time.sleep(random.uniform(0.5, 2))


class DetectionEvasion:
    """
    Advanced evasion techniques
    """
    
    @staticmethod
    def randomize_timing_pattern():
        """
        Returns a random session duration to avoid pattern detection
        """
        # Don't always run exactly 12 hours
        variations = [
            12 * 3600,      # Exactly 12 hours
            11.5 * 3600,    # 11.5 hours
            12.5 * 3600,    # 12.5 hours
            11 * 3600,      # 11 hours
            13 * 3600,      # 13 hours
        ]
        return random.choice(variations)
    
    @staticmethod
    def get_random_session_gap():
        """
        Random gap between sessions to avoid schedule detection
        """
        # Gap between 2-8 hours
        return random.randint(2 * 3600, 8 * 3600)
    
    @staticmethod
    def rotate_ip_proxy():
        """
        Placeholder for proxy rotation
        In production, would integrate with proxy service
        """
        proxies = [
            None,  # Use direct connection sometimes
            # Add proxy configurations here
        ]
        return random.choice(proxies)
    
    @staticmethod
    def random_user_behavior_schedule():
        """
        Generate random break patterns within session
        """
        schedule = []
        current_time = 0
        session_length = 12 * 3600  # 12 hours
        
        while current_time < session_length:
            # Work period
            work_duration = random.randint(1800, 7200)  # 30 min to 2 hours
            schedule.append(("work", work_duration))
            current_time += work_duration
            
            # Break period
            if current_time < session_length:
                break_duration = random.randint(300, 1800)  # 5-30 min
                schedule.append(("break", break_duration))
                current_time += break_duration
        
        return schedule


class AntiDetectionOrchestrator:
    """
    Orchestrates all anti-detection measures
    """
    
    def __init__(self):
        self.stealth_profile = StealthProfile()
        self.behavior_sim = None  # Created after driver init
        self.evasion = DetectionEvasion()
        self.detection_log = []
    
    def initialize_session(self, driver):
        """Apply all anti-detection measures to driver"""
        
        # Inject stealth JavaScript
        stealth_js = self.stealth_profile.get_stealth_js()
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': stealth_js
        })
        
        # Initialize behavior simulator
        self.behavior_sim = HumanBehaviorSimulator(self.stealth_profile)
        
        # Set viewport size
        driver.set_window_size(
            self.stealth_profile.profile['viewport'][0],
            self.stealth_profile.profile['viewport'][1]
        )
        
        print(f"✅ Anti-detection initialized")
        print(f"   Session ID: {self.stealth_profile.profile['session_id']}")
        print(f"   User Agent: {self.stealth_profile.profile['user_agent'][:50]}...")
        print(f"   Viewport: {self.stealth_profile.profile['viewport']}")
        print(f"   Timezone: {self.stealth_profile.profile['timezone']}")
    
    def log_detection_attempt(self, source: str, method: str, success: bool):
        """Log potential detection attempts"""
        self.detection_log.append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "method": method,
            "evaded": success
        })
    
    def get_session_summary(self) -> Dict:
        """Get summary of anti-detection measures used"""
        return {
            "session_id": self.stealth_profile.profile['session_id'],
            "fingerprint_hash": hashlib.md5(
                json.dumps(self.stealth_profile.profile, sort_keys=True).encode()
            ).hexdigest()[:16],
            "detection_attempts": len(self.detection_log),
            "evasion_success_rate": (
                sum(1 for d in self.detection_log if d['evaded']) / len(self.detection_log) * 100
                if self.detection_log else 100
            )
        }


def main():
    """Test anti-detection system"""
    print("="*70)
    print("  ANTI-DETECTION SYSTEM TEST")
    print("="*70)
    
    # Create orchestrator
    anti_detect = AntiDetectionOrchestrator()
    
    print("\n🎭 Stealth Profile Generated:")
    for key, value in anti_detect.stealth_profile.profile.items():
        if key != 'fonts':  # Skip long list
            print(f"   {key}: {value}")
    
    print("\n🔄 Session Schedule:")
    schedule = DetectionEvasion.random_user_behavior_schedule()
    total_time = sum(duration for _, duration in schedule)
    print(f"   Total activities: {len(schedule)}")
    print(f"   Total time: {total_time / 3600:.1f} hours")
    
    print("\n✅ Anti-detection system ready")
    print("="*70)


if __name__ == "__main__":
    main()
