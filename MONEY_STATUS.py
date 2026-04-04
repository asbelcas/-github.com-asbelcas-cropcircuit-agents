#!/usr/bin/env python3
"""
MONEY_STATUS.py - Revenue-First System Dashboard

Shows ONLY what matters: Are we making money?
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

def get_money_status():
    """Get complete money status"""
    
    status = {
        'revenue': {'today': 0, 'month': 0, 'goal_today': 100, 'goal_month': 2000},
        'assets': {'data': 0, 'products': 0, 'packages': 0},
        'activity': {'outreach': 0, 'proposals': 0, 'pending_value': 0},
        'processes': {}
    }
    
    # Check money_central.db
    if Path("/home/asbelcas/rm-qpt/money_central.db").exists():
        conn = sqlite3.connect("/home/asbelcas/rm-qpt/money_central.db")
        c = conn.cursor()
        
        # Revenue
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT SUM(amount) FROM money_in WHERE date(timestamp) = ?", (today,))
        status['revenue']['today'] = c.fetchone()[0] or 0
        
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        c.execute("SELECT SUM(amount) FROM money_in WHERE date(timestamp) >= ?", (month_start,))
        status['revenue']['month'] = c.fetchone()[0] or 0
        
        # Activity
        c.execute("SELECT COUNT(*) FROM outreach WHERE sent = 1")
        status['activity']['outreach'] = c.fetchone()[0] or 0
        
        c.execute("SELECT COUNT(*), SUM(value) FROM proposals WHERE status != 'draft'")
        result = c.fetchone()
        status['activity']['proposals'] = result[0] or 0
        status['activity']['pending_value'] = result[1] or 0
        
        conn.close()
    
    # Physical assets
    status['assets']['data'] = len(list(Path("/home/asbelcas/rm-qpt/collected_data").glob("*.json")))
    status['assets']['products'] = len(list(Path("/home/asbelcas/rm-qpt/generated_products").glob("*.py")))
    status['assets']['packages'] = len(list(Path("/home/asbelcas/rm-qpt/ready_to_sell").glob("*.zip")))
    
    # Processes
    import subprocess
    
    # Check REAL_SLEEP_MONEY
    result = subprocess.run(["pgrep", "-f", "REAL_SLEEP_MONEY.py"], capture_output=True, text=True)
    status['processes']['data_collector'] = 'running' if result.stdout.strip() else 'stopped'
    
    # Check MONEY_LOOP
    result = subprocess.run(["pgrep", "-f", "MONEY_LOOP.py"], capture_output=True, text=True)
    status['processes']['money_loop'] = 'running' if result.stdout.strip() else 'stopped'
    
    return status

def print_money_dashboard():
    """Print revenue-focused dashboard"""
    
    status = get_money_status()
    
    # Calculate metrics
    daily_pct = (status['revenue']['today'] / status['revenue']['goal_today']) * 100
    monthly_pct = (status['revenue']['month'] / status['revenue']['goal_month']) * 100
    hours_left = 24 - datetime.now().hour
    needed_hourly = max(0, (status['revenue']['goal_today'] - status['revenue']['today']) / hours_left) if hours_left > 0 else 0
    
    print("\n" + "="*70)
    print("💰 MONEY DASHBOARD - CROPCIRCUIT REVENUE SYSTEM")
    print("="*70)
    
    # REVENUE SECTION
    print("\n🎯 REVENUE (THE ONLY METRIC THAT MATTERS)")
    print("-"*70)
    
    # Today's revenue with color coding
    if daily_pct >= 100:
        daily_icon = "✅"
    elif daily_pct >= 50:
        daily_icon = "⚡"
    else:
        daily_icon = "🔥"
    
    print(f"{daily_icon} TODAY:     ${status['revenue']['today']:>7.2f} / ${status['revenue']['goal_today']:.0f} ({daily_pct:>5.1f}%)")
    
    if status['revenue']['today'] < status['revenue']['goal_today'] and hours_left > 0:
        print(f"   Need ${needed_hourly:.2f}/hour for next {hours_left}h to hit goal")
    
    # Monthly
    if monthly_pct >= 100:
        monthly_icon = "✅"
    elif monthly_pct >= 50:
        monthly_icon = "📈"
    else:
        monthly_icon = "🚀"
    
    print(f"{monthly_icon} THIS MONTH: ${status['revenue']['month']:>7.2f} / ${status['revenue']['goal_month']:.0f} ({monthly_pct:>5.1f}%)")
    
    # Pending
    if status['activity']['pending_value'] > 0:
        print(f"💼 PENDING:   ${status['activity']['pending_value']:.2f} in proposals")
    
    # ASSETS SECTION
    print("\n📦 ASSETS (Ready to convert to $)")
    print("-"*70)
    
    # Calculate potential value
    package_value = status['assets']['packages'] * 19  # $19 avg per package
    
    print(f"   Data Files:  {status['assets']['data']:>3} (intelligence)")
    print(f"   Products:    {status['assets']['products']:>3} (code)")
    print(f"   Packages:    {status['assets']['packages']:>3} (ready to sell = ${package_value})")
    
    # ACTIVITY SECTION
    print("\n🎯 MONEY-MAKING ACTIVITY")
    print("-"*70)
    
    print(f"   Outreach Sent:  {status['activity']['outreach']:>3}")
    print(f"   Proposals:      {status['activity']['proposals']:>3}")
    
    # Rate the activity level
    activity_score = status['activity']['outreach'] + (status['activity']['proposals'] * 3)
    if activity_score >= 10:
        activity_rating = "🔥 HIGH"
    elif activity_score >= 5:
        activity_rating = "⚡ MODERATE"
    else:
        activity_rating = "😴 LOW - NEED MORE ACTION"
    
    print(f"   Activity Level: {activity_rating}")
    
    # SYSTEM STATUS
    print("\n⚙️  SYSTEM STATUS")
    print("-"*70)
    
    for proc, state in status['processes'].items():
        icon = "✅" if state == 'running' else "❌"
        print(f"   {icon} {proc:20} {state}")
    
    # ACTIONS NEEDED
    print("\n🚨 ACTIONS TO MAKE MONEY NOW")
    print("-"*70)
    
    actions = []
    
    if status['revenue']['today'] == 0:
        actions.append(("CRITICAL", "Record a sale or send outreach NOW"))
    
    if status['assets']['packages'] > 0:
        actions.append(("HIGH", f"List {status['assets']['packages']} products on Gumroad"))
    
    if status['activity']['outreach'] < 5:
        actions.append(("HIGH", "Send 5 outreach messages to potential clients"))
    
    if status['processes']['money_loop'] == 'stopped':
        actions.append(("MEDIUM", "Start MONEY_LOOP: python3 MONEY_LOOP.py run"))
    
    for priority, action in actions[:5]:
        print(f"   [{priority:8}] {action}")
    
    # SUMMARY
    print("\n" + "="*70)
    
    if status['revenue']['today'] > 0:
        print(f"✅ MAKING MONEY: ${status['revenue']['today']:.2f} today")
    else:
        print("❌ NO REVENUE TODAY - TAKE ACTION NOW")
    
    print("="*70)

def print_quick_status():
    """One-line status for scripts"""
    status = get_money_status()
    
    print(f"💰 ${status['revenue']['today']:.0f}/{status['revenue']['goal_today']:.0f} today | " +
          f"${status['revenue']['month']:.0f}/{status['revenue']['goal_month']:.0f} month | " +
          f"{status['activity']['outreach']} outreach | " +
          f"{status['activity']['proposals']} proposals")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Money Status")
    parser.add_argument('--quick', action='store_true', help='One-line status')
    
    args = parser.parse_args()
    
    if args.quick:
        print_quick_status()
    else:
        print_money_dashboard()

if __name__ == "__main__":
    main()
