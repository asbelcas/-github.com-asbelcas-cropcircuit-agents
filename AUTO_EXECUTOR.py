#!/usr/bin/env python3
"""
CROP CIRCUIT - AUTO EXECUTOR v2.0
CONTINUOUS MODE with Safety Rails
For: Emergency time-constrained operations
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG = {
    "mode": "AUTONOMOUS",
    "max_daily_spend": 0,
    "risk_level": "LOW",
    "check_interval": 300,
    "human_checkin_hours": 4,
    "continuous": True,  # NEW: Run continuously
}

# Safety limits - HARD STOPS
SAFETY_LIMITS = {
    "can_spend_money": False,
    "can_access_accounts": False,
    "can_sign_contracts": False,
    "can_make_commitments": False,
    "can_share_personal_data": False,
    "can_automate_trading": False,
}

# What we CAN do autonomously
ALLOWED_ACTIONS = {
    "research": True,
    "create_profiles": True,
    "draft_proposals": True,
    "apply_to_jobs": True,
    "send_messages": True,
    "track_opportunities": True,
    "create_content": True,
    "analyze_data": True,
}

class AutoExecutor:
    def __init__(self):
        self.start_time = datetime.now()
        self.actions_taken = []
        self.status = "ACTIVE"
        self.log_file = f"/home/asbelcas/rm-qpt/logs/auto_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        self.pid_file = "/home/asbelcas/rm-qpt/auto_executor.pid"
        
        # Write PID file
        with open(self.pid_file, 'w') as f:
            f.write(str(os.getpid()))
        
        os.makedirs("/home/asbelcas/rm-qpt/logs", exist_ok=True)
        self.log("="*70)
        self.log("🤖 AUTO EXECUTOR v2.0 ACTIVATED - CONTINUOUS MODE")
        self.log("="*70)
        self.log(f"PID: {os.getpid()}")
        self.log(f"Start time: {self.start_time}")
        self.log(f"Mode: {CONFIG['mode']}")
        self.log(f"Risk level: {CONFIG['risk_level']}")
        self.log(f"Continuous: {CONFIG['continuous']}")
        self.log("="*70)
        
    def log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        with open(self.log_file, 'a') as f:
            f.write(line + "\n")
    
    def safety_check(self, action_type, details):
        if action_type not in ALLOWED_ACTIONS or not ALLOWED_ACTIONS[action_type]:
            self.log(f"❌ BLOCKED: {action_type} not in allowed actions")
            return False
        if "spend" in details.lower() or "buy" in details.lower() or "$" in details:
            if not SAFETY_LIMITS["can_spend_money"]:
                self.log(f"❌ BLOCKED: Spending action requires human approval")
                return False
        if "contract" in details.lower() or "agreement" in details.lower():
            if not SAFETY_LIMITS["can_make_commitments"]:
                self.log(f"❌ BLOCKED: Commitment requires human approval")
                return False
        return True
    
    def execute_action(self, action_type, description, func):
        self.log(f"\n{'='*70}")
        self.log(f"ACTION: {action_type}")
        self.log(f"Description: {description}")
        
        if not self.safety_check(action_type, description):
            self.actions_taken.append({
                "time": datetime.now().isoformat(),
                "type": action_type,
                "description": description,
                "status": "BLOCKED_BY_SAFETY"
            })
            return False
        
        try:
            result = func()
            self.log(f"✅ SUCCESS: {result}")
            self.actions_taken.append({
                "time": datetime.now().isoformat(),
                "type": action_type,
                "description": description,
                "status": "SUCCESS",
                "result": str(result)
            })
            return True
        except Exception as e:
            self.log(f"❌ ERROR: {e}")
            self.actions_taken.append({
                "time": datetime.now().isoformat(),
                "type": action_type,
                "description": description,
                "status": "ERROR",
                "error": str(e)
            })
            return False
    
    def action_check_opportunities(self):
        """Check for new freelance opportunities"""
        def _check():
            # Simulate checking job boards
            # In real implementation, would scrape Upwork/Fiverr
            opportunities_found = 0  # Placeholder
            return f"Checked for opportunities. Found: {opportunities_found} new."
        return self.execute_action("research", "Check for new job opportunities", _check)
    
    def action_monitor_status(self):
        """Generate periodic status report"""
        def _monitor():
            runtime = datetime.now() - self.start_time
            hours = runtime.seconds // 3600
            
            # Save status
            status = {
                "timestamp": datetime.now().isoformat(),
                "runtime_hours": hours,
                "actions_count": len(self.actions_taken),
                "status": "RUNNING",
                "pid": os.getpid()
            }
            
            with open("/home/asbelcas/rm-qpt/current_status.json", "w") as f:
                json.dump(status, f, indent=2)
            
            return f"Status updated. Runtime: {hours}h, Actions: {len(self.actions_taken)}"
        return self.execute_action("track_opportunities", "Monitor and log status", _monitor)
    
    def action_heartbeat(self):
        """Simple heartbeat to show system is alive"""
        self.log(f"💓 Heartbeat: {datetime.now().strftime('%H:%M:%S')} - System active")
        return True
    
    def run(self):
        """Main continuous execution loop"""
        self.log(f"\nStarting continuous monitoring")
        self.log(f"Check interval: {CONFIG['check_interval']} seconds")
        self.log(f"Press Ctrl+C to stop")
        self.log("="*70)
        
        # Initial setup actions
        self.log("\nPerforming initial setup...")
        self.action_monitor_status()
        
        iteration = 0
        try:
            while CONFIG['continuous']:
                iteration += 1
                self.log(f"\n--- Iteration {iteration} ---")
                
                # Regular actions
                if iteration % 1 == 0:  # Every iteration
                    self.action_heartbeat()
                
                if iteration % 12 == 0:  # Every hour (12 * 5 min = 60 min)
                    self.action_check_opportunities()
                
                if iteration % 6 == 0:  # Every 30 minutes
                    self.action_monitor_status()
                
                # Save state
                self._save_state()
                
                # Sleep
                self.log(f"Sleeping {CONFIG['check_interval']} seconds...")
                time.sleep(CONFIG['check_interval'])
                
        except KeyboardInterrupt:
            self.log("\n🛑 Stopped by user")
        except Exception as e:
            self.log(f"\n❌ Fatal error: {e}")
        finally:
            self._cleanup()
    
    def _save_state(self):
        """Save current state"""
        state = {
            "start_time": self.start_time.isoformat(),
            "last_update": datetime.now().isoformat(),
            "actions": self.actions_taken[-50:],  # Last 50 actions
            "status": self.status,
            "pid": os.getpid()
        }
        with open("/home/asbelcas/rm-qpt/auto_executor_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def _cleanup(self):
        """Cleanup on exit"""
        self.log("\nCleaning up...")
        self._save_state()
        
        # Remove PID file
        if os.path.exists(self.pid_file):
            os.remove(self.pid_file)
        
        self.log("Status: STOPPED")
        self.log(f"Total actions: {len(self.actions_taken)}")
        self.log("="*70)


def main():
    print("="*70)
    print("🤖 CROP CIRCUIT - AUTO EXECUTOR v2.0")
    print("="*70)
    print()
    print("Mode: AUTONOMOUS (with safety rails)")
    print("Type: CONTINUOUS (runs until stopped)")
    print("Risk Level: LOW")
    print("Spending: DISABLED")
    print()
    
    executor = AutoExecutor()
    executor.run()
    
    print("\n✅ Auto executor stopped")


if __name__ == "__main__":
    main()
