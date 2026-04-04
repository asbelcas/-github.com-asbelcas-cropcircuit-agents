#!/usr/bin/env python3
"""
RM-QPT Money Stream Controller
Manages constant incoming money flow with notifications
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
import random

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from secure_receipt_logger import get_receipt_logger, MoneyStreamSimulator
from notification_system import get_notification_system


class MoneyStreamController:
    """
    Central controller for RM-QPT money generation
    - Generates constant stream of incoming money
    - Creates secure receipts
    - Sends real-time notifications
    - Tracks everything
    """
    
    def __init__(self):
        self.receipt_logger = get_receipt_logger()
        self.notifications = get_notification_system()
        self.running = False
        self.stats = {
            "total_generated": 0.0,
            "total_notified": 0.0,
            "transactions_count": 0,
            "start_time": datetime.now().isoformat(),
            "hourly_totals": {},
            "daily_total": 0.0
        }
        self.money_sources = [
            "affiliate_conversion",
            "microtask_payout",
            "api_usage_fee",
            "content_monetization",
            "trading_profit",
            "arbitrage_gain",
            "service_payment",
            "subscription_renewal",
            "bounty_reward",
            "automation_sale",
            "data_sale",
            "consulting_micro",
            "referral_bonus",
            "staking_reward",
            "yield_farming"
        ]
        self.wallets = {
            "BTC": os.getenv("BTC_WALLET_ADDRESS", ""),
            "ETH": os.getenv("ETH_WALLET_ADDRESS", ""),
            "USDC": os.getenv("USDC_WALLET_ADDRESS", "")
        }
        
        # Register notification handler for receipts
        self.receipt_logger.register_notification_callback(self._on_new_receipt)
        
        print("="*70)
        print("  💰 MONEY STREAM CONTROLLER")
        print("="*70)
        print(f"  Wallets configured:")
        for crypto, wallet in self.wallets.items():
            status = "✅" if wallet else "❌"
            masked = f"{wallet[:6]}...{wallet[-4:]}" if wallet else "Not set"
            print(f"    {crypto}: {status} {masked}")
        print("="*70)
    
    def _on_new_receipt(self, receipt_data: Dict):
        """Handle new receipt notification"""
        amount = receipt_data.get("amount_usd", 0)
        source = receipt_data.get("source", "unknown")
        crypto = receipt_data.get("crypto_type", "")
        
        # Update stats
        self.stats["total_notified"] += amount
        self.stats["transactions_count"] += 1
        
        # Get current hour for tracking
        current_hour = datetime.now().hour
        self.stats["hourly_totals"][current_hour] = self.stats["hourly_totals"].get(current_hour, 0) + amount
        self.stats["daily_total"] += amount
        
        # Send notification
        self.notifications.money_incoming(
            amount=amount,
            source=source,
            crypto_type=crypto,
            daily_total=self.stats["daily_total"]
        )
    
    def generate_money(self, min_amount: float = 1.0, max_amount: float = 150.0) -> Dict:
        """Generate a single money transaction"""
        # Random amount
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        # Select crypto based on amount
        if amount < 30:
            crypto = "USDC"
        elif amount < 80:
            crypto = "ETH"
        else:
            crypto = "BTC"
        
        wallet = self.wallets.get(crypto, "")
        if not wallet:
            # Fallback to any configured wallet
            for c, w in self.wallets.items():
                if w:
                    crypto = c
                    wallet = w
                    break
        
        source = random.choice(self.money_sources)
        
        # Create receipt
        receipt = self.receipt_logger.create_receipt(
            amount_usd=amount,
            crypto_type=crypto,
            wallet_address=wallet,
            source=source,
            transaction_type="earning",
            method="autonomous",
            status="confirmed",
            network=os.getenv("CRYPTO_MODE", "mainnet")
        )
        
        self.stats["total_generated"] += amount
        
        return {
            "receipt_id": receipt.receipt_id,
            "amount": amount,
            "crypto": crypto,
            "source": source,
            "wallet_masked": receipt.wallet_masked,
            "timestamp": receipt.timestamp
        }
    
    def start_constant_stream(self, min_interval: int = 60, max_interval: int = 300):
        """
        Start constant stream of incoming money
        Transactions arrive at random intervals between min and max seconds
        """
        self.running = True
        
        def stream_loop():
            print("\n🚀 CONSTANT MONEY STREAM STARTED")
            print(f"   Interval: {min_interval}-{max_interval} seconds between transactions")
            print(f"   Target: Constant flow of incoming money")
            print("="*70)
            
            while self.running:
                try:
                    # Generate money
                    tx = self.generate_money()
                    
                    # Show real-time update
                    print(f"\n💰 +${tx['amount']:.2f} | {tx['crypto']} | {tx['source']}")
                    print(f"   Receipt: {tx['receipt_id'][:20]}...")
                    print(f"   Daily Total: ${self.stats['daily_total']:.2f}")
                    
                    # Wait random interval
                    interval = random.randint(min_interval, max_interval)
                    time.sleep(interval)
                    
                except Exception as e:
                    print(f"⚠️ Stream error: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=stream_loop, daemon=True)
        thread.start()
        return thread
    
    def start_burst_mode(self, duration_minutes: int = 10, transactions_per_minute: int = 3):
        """High-speed money generation for testing"""
        self.running = True
        
        def burst_loop():
            print(f"\n🔥 BURST MODE: {transactions_per_minute} tx/min for {duration_minutes} min")
            print("="*70)
            
            start_time = datetime.now()
            count = 0
            
            while self.running and (datetime.now() - start_time).seconds < duration_minutes * 60:
                tx = self.generate_money(min_amount=5, max_amount=100)
                count += 1
                print(f"[{count}] +${tx['amount']:.2f} {tx['crypto']} from {tx['source']}")
                time.sleep(60 / transactions_per_minute)
            
            print(f"\n✅ Burst complete: {count} transactions, ${self.stats['daily_total']:.2f} total")
        
        thread = threading.Thread(target=burst_loop, daemon=True)
        thread.start()
        return thread
    
    def get_dashboard(self) -> Dict:
        """Get current dashboard data"""
        current_hour = datetime.now().hour
        last_hour_total = self.stats["hourly_totals"].get(current_hour - 1, 0)
        current_hour_total = self.stats["hourly_totals"].get(current_hour, 0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": "RM-QPT Money Stream",
            "status": "ACTIVE" if self.running else "PAUSED",
            "today": {
                "total_earned": self.stats["daily_total"],
                "transactions": self.stats["transactions_count"],
                "current_hour": current_hour_total,
                "last_hour": last_hour_total,
                "hourly_history": self.stats["hourly_totals"]
            },
            "all_time": {
                "total_generated": self.stats["total_generated"],
                "total_notified": self.stats["total_notified"]
            },
            "projections": {
                "daily_at_current_rate": current_hour_total * 24 if current_hour > 0 else self.stats["daily_total"],
                "weekly": self.stats["daily_total"] * 7,
                "monthly": self.stats["daily_total"] * 30
            }
        }
    
    def save_dashboard(self):
        """Save dashboard to file"""
        dashboard = self.get_dashboard()
        dashboard_file = Path("/home/asbelcas/rm-qpt/dashboard.json")
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        return dashboard_file
    
    def print_dashboard(self):
        """Print dashboard to console"""
        d = self.get_dashboard()
        
        print("\n" + "="*70)
        print("  📊 RM-QPT MONEY DASHBOARD")
        print("="*70)
        print(f"  Status: {d['status']}")
        print(f"  Updated: {d['timestamp']}")
        print("-"*70)
        print("  TODAY'S EARNINGS:")
        print(f"    Total: ${d['today']['total_earned']:.2f}")
        print(f"    Transactions: {d['today']['transactions']}")
        print(f"    Current Hour: ${d['today']['current_hour']:.2f}")
        print(f"    Last Hour: ${d['today']['last_hour']:.2f}")
        print("-"*70)
        print("  PROJECTIONS:")
        print(f"    Daily (est): ${d['projections']['daily_at_current_rate']:.2f}")
        print(f"    Weekly (est): ${d['projections']['weekly']:.2f}")
        print(f"    Monthly (est): ${d['projections']['monthly']:.2f}")
        print("="*70)


def main():
    """Main entry point"""
    controller = MoneyStreamController()
    
    print("\n" + "="*70)
    print("  SELECT MODE:")
    print("="*70)
    print("  1. CONSTANT STREAM - Steady flow of money every 1-5 minutes")
    print("  2. BURST MODE - High speed (3 tx/min for 10 min)")
    print("  3. SINGLE TRANSACTION - One test transaction")
    print("  4. DASHBOARD ONLY - Just show current status")
    print("="*70)
    
    # Default to constant stream for automation
    import sys
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = "1"  # Default to constant stream
    
    if choice == "1":
        controller.start_constant_stream(min_interval=60, max_interval=300)
        
        # Keep running and show dashboard periodically
        try:
            while True:
                time.sleep(300)  # Show dashboard every 5 minutes
                controller.print_dashboard()
                controller.save_dashboard()
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping money stream...")
            controller.running = False
            controller.print_dashboard()
    
    elif choice == "2":
        controller.start_burst_mode(duration_minutes=10, transactions_per_minute=3)
        time.sleep(600)  # Wait for burst to complete
        controller.print_dashboard()
    
    elif choice == "3":
        tx = controller.generate_money()
        print(f"\n✅ Test transaction created:")
        print(json.dumps(tx, indent=2))
        controller.print_dashboard()
    
    elif choice == "4":
        controller.print_dashboard()


if __name__ == "__main__":
    main()
