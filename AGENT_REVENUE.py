#!/usr/bin/env python3
"""
AGENT REVENUE MODULE

Handles all money-making operations.

NO FAKE DATA. NO SIMULATIONS. REAL REVENUE ONLY.

Current capabilities:
- Track product sales (manual entry when items sell)
- Track service revenue (when clients pay)
- Calculate actual ROI
- Report on real income

Required for full automation:
- Stripe/PayPal account + API keys
- Marketplace seller accounts
- Business bank account for payouts
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

REVENUE_DB = "/home/asbelcas/rm-qpt/agent_central.db"

class RevenueTracker:
    """Track actual, confirmed revenue ONLY"""
    
    def __init__(self):
        self.db_path = REVENUE_DB
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure revenue tracking tables exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Real revenue only - confirmed payments
        c.execute('''CREATE TABLE IF NOT EXISTS confirmed_revenue (
            id INTEGER PRIMARY KEY,
            date TEXT,
            source TEXT,
            platform TEXT,
            item_type TEXT,
            description TEXT,
            amount REAL,
            fee_amount REAL DEFAULT 0,
            net_amount REAL,
            transaction_id TEXT,
            proof_file TEXT,
            notes TEXT
        )''')
        
        # Pending payments (not yet confirmed)
        c.execute('''CREATE TABLE IF NOT EXISTS pending_payments (
            id INTEGER PRIMARY KEY,
            expected_date TEXT,
            source TEXT,
            description TEXT,
            expected_amount REAL,
            status TEXT DEFAULT 'pending',
            actual_revenue_id INTEGER
        )''')
        
        conn.commit()
        conn.close()
    
    def add_sale(self, platform, item_type, description, amount, 
                 transaction_id=None, proof_file=None):
        """
        Add a CONFIRMED sale.
        
        Use this ONLY when you have proof of sale (email, dashboard screenshot)
        """
        # Calculate fees
        fee_rates = {
            'gumroad': 0.10,      # 10% fee
            'etsy': 0.065,        # 6.5% fee  
            'upwork': 0.20,       # 20% fee
            'stripe': 0.029,      # 2.9% + $0.30
            'paypal': 0.034,      # 3.4% + $0.30
            'direct': 0.0
        }
        
        fee_rate = fee_rates.get(platform.lower(), 0.10)
        fee_amount = amount * fee_rate
        net_amount = amount - fee_amount
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO confirmed_revenue 
            (date, source, platform, item_type, description, amount, 
             fee_amount, net_amount, transaction_id, proof_file, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (datetime.now().isoformat(),
             platform.lower(),
             platform,
             item_type,
             description,
             amount,
             fee_amount,
             net_amount,
             transaction_id,
             proof_file,
             'Manually confirmed by operator'))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Recorded sale: ${amount:.2f} on {platform}")
        print(f"   Fee: ${fee_amount:.2f} | Net: ${net_amount:.2f}")
    
    def get_report(self, days=30):
        """Generate revenue report for last N days"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Overall stats
        c.execute('''SELECT 
            COUNT(*),
            SUM(amount),
            SUM(net_amount),
            AVG(amount)
            FROM confirmed_revenue 
            WHERE date > ?''', (since,))
        
        total_count, total_gross, total_net, avg_sale = c.fetchone()
        
        # By platform
        c.execute('''SELECT 
            platform,
            COUNT(*),
            SUM(amount),
            SUM(net_amount)
            FROM confirmed_revenue 
            WHERE date > ?
            GROUP BY platform''', (since,))
        
        by_platform = c.fetchall()
        
        # Daily breakdown (last 7 days)
        c.execute('''SELECT 
            date(date) as day,
            COUNT(*),
            SUM(net_amount)
            FROM confirmed_revenue
            WHERE date > ?
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7''', (since,))
        
        daily = c.fetchall()
        
        conn.close()
        
        # Print report
        print("\n" + "="*70)
        print(f"📊 REVENUE REPORT - Last {days} Days")
        print("="*70)
        
        if total_count == 0:
            print("\n   ❌ NO CONFIRMED REVENUE")
            print("\n   Your products exist but haven't sold yet.")
            print("   Next steps:")
            print("   1. List products on marketplaces")
            print("   2. Share on social media")
            print("   3. Send direct outreach")
            return
        
        print(f"\n💰 TOTALS:")
        print(f"   Sales:       {total_count}")
        print(f"   Gross:       ${total_gross:.2f}")
        print(f"   Net:         ${total_net:.2f}")
        print(f"   Avg Sale:    ${avg_sale:.2f}")
        
        print(f"\n🏢 BY PLATFORM:")
        for platform, count, gross, net in by_platform:
            print(f"   {platform:12} {count:3} sales  ${gross:8.2f} gross  ${net:8.2f} net")
        
        print(f"\n📅 DAILY (Last 7 days):")
        for day, count, net in daily:
            print(f"   {day}  {count:2} sales  ${net:7.2f} net")
        
        print("="*70)
    
    def show_dashboard(self):
        """Live revenue dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Lifetime stats
        c.execute('''SELECT 
            COUNT(*),
            SUM(amount),
            SUM(net_amount)
            FROM confirmed_revenue''')
        
        lifetime = c.fetchone()
        
        # Today
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT 
            COUNT(*),
            SUM(net_amount)
            FROM confirmed_revenue
            WHERE date(date) = ?''', (today,))
        
        today_stats = c.fetchone()
        
        # Pending payments
        c.execute('''SELECT 
            COUNT(*),
            SUM(expected_amount)
            FROM pending_payments
            WHERE status = 'pending'
            AND expected_date <= date('now', '+7 days')''')
        
        pending = c.fetchone()
        
        conn.close()
        
        print("\n" + "="*70)
        print("💵 REVENUE DASHBOARD")
        print("="*70)
        print(f"\n   Lifetime Revenue:")
        print(f"      Sales:    {lifetime[0] or 0}")
        print(f"      Gross:    ${lifetime[1] or 0:.2f}")
        print(f"      Net:      ${lifetime[2] or 0:.2f}")
        
        print(f"\n   Today ({today}):")
        print(f"      Sales:    {today_stats[0] or 0}")
        print(f"      Net:      ${today_stats[1] or 0:.2f}")
        
        print(f"\n   Expected Soon:")
        print(f"      Payments: {pending[0] or 0}")
        print(f"      Amount:   ${pending[1] or 0:.2f}")
        
        print("="*70)

class ActionPlanner:
    """Plan actions based on revenue goals"""
    
    def __init__(self, monthly_goal=500):
        self.monthly_goal = monthly_goal
        self.revenue = RevenueTracker()
    
    def recommend_actions(self):
        """Recommend next actions based on current state"""
        conn = sqlite3.connect(REVENUE_DB)
        c = conn.cursor()
        
        # Current month progress
        month_start = datetime.now().replace(day=1).isoformat()
        c.execute('''SELECT SUM(net_amount) FROM confirmed_revenue 
            WHERE date > ?''', (month_start,))
        
        current = c.fetchone()[0] or 0
        progress = (current / self.monthly_goal) * 100
        
        # Pending tasks
        c.execute('''SELECT COUNT(*) FROM tasks WHERE status = 'pending'
            AND type IN ('packaging', 'listing')''')
        pending_sales_tasks = c.fetchone()[0]
        
        # Assets ready
        products = len(list(Path("generated_products").glob("*.py")))
        packages = len(list(Path("ready_to_sell").glob("*.zip")))
        unlisted = products - packages
        
        conn.close()
        
        print("\n" + "="*70)
        print(f"🎯 ACTION PLANNER")
        print("="*70)
        print(f"\n   Goal: ${self.monthly_goal}/month")
        print(f"   Current: ${current:.2f} ({progress:.1f}%)")
        
        print(f"\n   📦 Assets:")
        print(f"      Products:   {products}")
        print(f"      Packaged:   {packages}")
        print(f"      Unlisted:   {unlisted}")
        
        print(f"\n   🎯 RECOMMENDED ACTIONS:")
        
        if unlisted > 0:
            priority = 10 if progress < 25 else 5
            print(f"   [{priority}/10] Package {unlisted} products for sale")
            print(f"      Command: python3 MAKE_MONEY_PRACTICAL.py package")
        
        if packages > 0 and current == 0:
            print(f"   [10/10] LIST PRODUCTS ON MARKETPLACE")
            print(f"      You have {packages} packages ready but $0 revenue")
            print(f"      Go to: https://gumroad.com")
            print(f"      Or: https://etsy.com/sell")
        
        if current > 0 and current < self.monthly_goal * 0.5:
            print(f"   [8/10] MARKETING - Share products on social media")
            print(f"      Post on Twitter/X, Reddit, IndieHackers")
        
        if pending_sales_tasks > 0:
            print(f"   [7/10] Execute {pending_sales_tasks} pending sales tasks")
        
        print("="*70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Revenue tracking and planning")
    parser.add_argument('action', choices=['add', 'report', 'dashboard', 'plan'])
    parser.add_argument('--platform', help='Platform name')
    parser.add_argument('--amount', type=float, help='Sale amount')
    parser.add_argument('--desc', help='Description')
    parser.add_argument('--type', default='product', help='Item type')
    parser.add_argument('--days', type=int, default=30, help='Report days')
    
    args = parser.parse_args()
    
    revenue = RevenueTracker()
    
    if args.action == 'add':
        if not args.platform or not args.amount or not args.desc:
            print("Error: --platform, --amount, and --desc required for add")
            sys.exit(1)
        revenue.add_sale(args.platform, args.type, args.desc, args.amount)
    
    elif args.action == 'report':
        revenue.get_report(args.days)
    
    elif args.action == 'dashboard':
        revenue.show_dashboard()
    
    elif args.action == 'plan':
        planner = ActionPlanner()
        planner.recommend_actions()

if __name__ == "__main__":
    main()
