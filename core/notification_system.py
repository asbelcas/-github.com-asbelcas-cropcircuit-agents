#!/usr/bin/env python3
"""
RM-QPT Real-Time Notification System
Multi-channel alerts for incoming money
"""

import os
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
import queue

NOTIFICATIONS_DIR = Path("/home/asbelcas/rm-qpt/notifications")
ALERTS_FILE = NOTIFICATIONS_DIR / "active_alerts.json"
NOTIFICATIONS_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Alert:
    """Alert configuration"""
    alert_id: str
    alert_type: str  # threshold, frequency, anomaly
    condition: str   # >, <, =, every
    threshold: float
    message_template: str
    channels: List[str]  # console, file, webhook, desktop
    enabled: bool = True
    last_triggered: Optional[str] = None
    trigger_count: int = 0


class NotificationSystem:
    """
    Real-time notification system for RM-QPT
    Handles alerts for incoming money, milestones, and status changes
    """
    
    NOTIFICATION_LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "SUCCESS": 2,
        "WARNING": 3,
        "ALERT": 4,
        "CRITICAL": 5
    }
    
    def __init__(self, min_level: str = "INFO"):
        self.min_level = self.NOTIFICATION_LEVELS.get(min_level, 1)
        self.notification_queue = queue.Queue()
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.stats = {
            "total_notifications": 0,
            "by_level": {k: 0 for k in self.NOTIFICATION_LEVELS.keys()},
            "by_channel": {}
        }
        
        # Default handlers
        self.register_handler("console", self._console_handler)
        self.register_handler("file", self._file_handler)
        self.register_handler("dashboard", self._dashboard_handler)
        
        # Alert configurations
        self.alerts: Dict[str, Alert] = {}
        self._load_alerts()
        self._setup_default_alerts()
        
        # Start notification processor
        self._start_processor()
        
        print("🔔 Notification System Initialized")
        print(f"   Min Level: {min_level}")
        print(f"   Handlers: {list(self.handlers.keys())}")
    
    def _load_alerts(self):
        """Load alert configurations"""
        if ALERTS_FILE.exists():
            try:
                with open(ALERTS_FILE) as f:
                    data = json.load(f)
                for alert_data in data.get("alerts", []):
                    alert = Alert(**alert_data)
                    self.alerts[alert.alert_id] = alert
            except Exception as e:
                print(f"⚠️ Error loading alerts: {e}")
    
    def _save_alerts(self):
        """Save alert configurations"""
        data = {
            "updated_at": datetime.now().isoformat(),
            "alerts": [self._alert_to_dict(a) for a in self.alerts.values()]
        }
        with open(ALERTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _alert_to_dict(self, alert: Alert) -> Dict:
        return {
            "alert_id": alert.alert_id,
            "alert_type": alert.alert_type,
            "condition": alert.condition,
            "threshold": alert.threshold,
            "message_template": alert.message_template,
            "channels": alert.channels,
            "enabled": alert.enabled,
            "last_triggered": alert.last_triggered,
            "trigger_count": alert.trigger_count
        }
    
    def _setup_default_alerts(self):
        """Setup default money alerts"""
        default_alerts = [
            Alert(
                alert_id="money_incoming",
                alert_type="threshold",
                condition=">",
                threshold=0.01,
                message_template="💰 +${amount:.2f} incoming! Total today: ${daily_total:.2f}",
                channels=["console", "file", "dashboard"]
            ),
            Alert(
                alert_id="daily_milestone_100",
                alert_type="threshold",
                condition=">=",
                threshold=100.0,
                message_template="🎯 DAILY MILESTONE: ${amount:.2f} reached! Keep it flowing!",
                channels=["console", "file", "dashboard"]
            ),
            Alert(
                alert_id="daily_milestone_500",
                alert_type="threshold",
                condition=">=",
                threshold=500.0,
                message_template="🔥 $500 DAY! Exceptional performance! Total: ${amount:.2f}",
                channels=["console", "file", "dashboard"]
            ),
            Alert(
                alert_id="hourly_check",
                alert_type="frequency",
                condition="every",
                threshold=3600,  # 1 hour
                message_template="⏰ Hourly check: ${hourly_total:.2f} this hour, ${daily_total:.2f} today",
                channels=["file", "dashboard"]
            ),
            Alert(
                alert_id="no_money_warning",
                alert_type="anomaly",
                condition="<",
                threshold=0.01,
                message_template="⚠️ WARNING: No money in last hour! Investigating...",
                channels=["console", "file"]
            ),
            Alert(
                alert_id="big_transaction",
                alert_type="threshold",
                condition=">",
                threshold=100.0,
                message_template="🚀 BIG ONE! +${amount:.2f} from {source}!",
                channels=["console", "file", "dashboard"]
            )
        ]
        
        for alert in default_alerts:
            if alert.alert_id not in self.alerts:
                self.alerts[alert.alert_id] = alert
        
        self._save_alerts()
    
    def register_handler(self, name: str, handler: Callable):
        """Register a notification handler"""
        self.handlers[name] = handler
        self.stats["by_channel"][name] = 0
    
    def _start_processor(self):
        """Start the notification processor thread"""
        self.running = True
        
        def processor():
            while self.running:
                try:
                    notification = self.notification_queue.get(timeout=1)
                    self._process_notification(notification)
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"⚠️ Notification processor error: {e}")
        
        thread = threading.Thread(target=processor, daemon=True)
        thread.start()
    
    def _process_notification(self, notification: Dict):
        """Process a single notification"""
        level = notification.get("level", "INFO")
        level_value = self.NOTIFICATION_LEVELS.get(level, 1)
        
        if level_value < self.min_level:
            return
        
        channels = notification.get("channels", ["console"])
        
        for channel in channels:
            if channel in self.handlers:
                try:
                    self.handlers[channel](notification)
                    self.stats["by_channel"][channel] = self.stats["by_channel"].get(channel, 0) + 1
                except Exception as e:
                    print(f"⚠️ Handler {channel} error: {e}")
        
        self.stats["total_notifications"] += 1
        self.stats["by_level"][level] = self.stats["by_level"].get(level, 0) + 1
    
    # Handlers
    def _console_handler(self, notification: Dict):
        """Print to console"""
        message = notification.get("message", "")
        level = notification.get("level", "INFO")
        
        # Color codes
        colors = {
            "DEBUG": "\033[90m",    # Gray
            "INFO": "\033[94m",     # Blue
            "SUCCESS": "\033[92m",  # Green
            "WARNING": "\033[93m",  # Yellow
            "ALERT": "\033[91m",    # Red
            "CRITICAL": "\033[95m", # Magenta
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        print(f"\n{color}[{timestamp}] [{level}]{reset} {message}")
    
    def _file_handler(self, notification: Dict):
        """Save to notification file"""
        notif_file = NOTIFICATIONS_DIR / f"notif_{datetime.now().strftime('%y%m%d')}.jsonl"
        
        with open(notif_file, 'a') as f:
            json.dump({
                **notification,
                "logged_at": datetime.now().isoformat()
            }, f)
            f.write('\n')
    
    def _dashboard_handler(self, notification: Dict):
        """Update dashboard file"""
        dashboard_file = NOTIFICATIONS_DIR / "dashboard.json"
        
        data = {
            "last_updated": datetime.now().isoformat(),
            "last_notification": notification,
            "stats": self.stats
        }
        
        with open(dashboard_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # Public methods
    def notify(self, message: str, level: str = "INFO", channels: List[str] = None, data: Dict = None):
        """Send a notification"""
        notification = {
            "message": message,
            "level": level,
            "channels": channels or ["console", "file"],
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }
        self.notification_queue.put(notification)
    
    def money_incoming(self, amount: float, source: str = "unknown", crypto_type: str = "", daily_total: float = 0):
        """Notify about incoming money"""
        # Check alerts
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
            
            if alert.alert_id == "money_incoming" and amount > 0:
                self._trigger_alert(alert, {"amount": amount, "source": source, "daily_total": daily_total})
            
            elif alert.alert_id == "big_transaction" and amount >= alert.threshold:
                self._trigger_alert(alert, {"amount": amount, "source": source})
            
            elif alert.alert_id == "daily_milestone_100" and daily_total >= 100:
                if not hasattr(self, '_milestone_100_triggered'):
                    self._trigger_alert(alert, {"amount": daily_total})
                    self._milestone_100_triggered = True
            
            elif alert.alert_id == "daily_milestone_500" and daily_total >= 500:
                if not hasattr(self, '_milestone_500_triggered'):
                    self._trigger_alert(alert, {"amount": daily_total})
                    self._milestone_500_triggered = True
        
        # Always send basic notification
        self.notify(
            message=f"💰 +${amount:.2f} from {source}",
            level="SUCCESS",
            channels=["console", "file", "dashboard"],
            data={"amount": amount, "source": source, "crypto": crypto_type, "daily_total": daily_total}
        )
    
    def _trigger_alert(self, alert: Alert, context: Dict):
        """Trigger an alert"""
        message = alert.message_template.format(**context)
        self.notify(message, "ALERT", alert.channels, {"alert_id": alert.alert_id, **context})
        
        alert.last_triggered = datetime.now().isoformat()
        alert.trigger_count += 1
        self._save_alerts()
    
    def hourly_check(self, hourly_total: float, daily_total: float):
        """Send hourly status update"""
        alert = self.alerts.get("hourly_check")
        if alert and alert.enabled:
            self._trigger_alert(alert, {"hourly_total": hourly_total, "daily_total": daily_total})
    
    def get_stats(self) -> Dict:
        """Get notification statistics"""
        return {
            **self.stats,
            "queue_size": self.notification_queue.qsize(),
            "alerts_configured": len(self.alerts),
            "alerts_enabled": sum(1 for a in self.alerts.values() if a.enabled)
        }
    
    def get_recent_notifications(self, count: int = 10) -> List[Dict]:
        """Get recent notifications from file"""
        notif_file = NOTIFICATIONS_DIR / f"notif_{datetime.now().strftime('%y%m%d')}.jsonl"
        
        if not notif_file.exists():
            return []
        
        notifications = []
        try:
            with open(notif_file) as f:
                for line in f:
                    notifications.append(json.loads(line.strip()))
        except:
            pass
        
        return notifications[-count:]


# Global instance
_notification_system = None

def get_notification_system() -> NotificationSystem:
    """Get singleton notification system"""
    global _notification_system
    if _notification_system is None:
        _notification_system = NotificationSystem()
    return _notification_system


if __name__ == "__main__":
    # Test
    ns = get_notification_system()
    
    print("\n" + "="*60)
    print("  NOTIFICATION SYSTEM TEST")
    print("="*60)
    
    # Test notifications
    ns.notify("System started", "INFO")
    ns.money_incoming(25.50, "affiliate", "USDC", 25.50)
    ns.money_incoming(150.00, "trading", "ETH", 175.50)
    
    time.sleep(1)
    
    print("\n" + "="*60)
    print("  STATS")
    print("="*60)
    print(json.dumps(ns.get_stats(), indent=2))
