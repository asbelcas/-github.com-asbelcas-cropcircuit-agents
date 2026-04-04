#!/usr/bin/env python3
"""
Agent Monitor - Health checks and diagnostics
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

def check_process():
    """Check if REAL_SLEEP_MONEY is running"""
    result = subprocess.run(
        ["pgrep", "-f", "REAL_SLEEP_MONEY.py"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        pid = result.stdout.strip().split('\n')[0]
        uptime = subprocess.run(
            ["ps", "-o", "etime=", "-p", pid],
            capture_output=True, text=True
        ).stdout.strip()
        return True, pid, uptime
    return False, None, None

def check_databases():
    """Check database health"""
    issues = []
    
    # Check agent_central.db
    if not Path("agent_central.db").exists():
        issues.append("agent_central.db missing")
    else:
        try:
            conn = sqlite3.connect('agent_central.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
            pending = c.fetchone()[0]
            conn.close()
        except Exception as e:
            issues.append(f"agent_central.db error: {e}")
    
    # Check real_sleep_money.db
    if not Path("real_sleep_money.db").exists():
        issues.append("real_sleep_money.db missing")
    else:
        try:
            conn = sqlite3.connect('real_sleep_money.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM actions")
            conn.close()
        except Exception as e:
            issues.append(f"real_sleep_money.db error: {e}")
    
    return issues

def check_assets():
    """Check asset consistency"""
    data = len(list(Path("collected_data").glob("*.json")))
    products = len(list(Path("generated_products").glob("*.py")))
    packages = len(list(Path("ready_to_sell").glob("*.zip")))
    
    issues = []
    if data == 0:
        issues.append("No data files")
    if products == 0:
        issues.append("No products")
    if products > packages:
        issues.append(f"{products - packages} products not packaged")
    
    return issues, data, products, packages

def main():
    print("="*70)
    print(f"AGENT MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()
    
    # Process check
    running, pid, uptime = check_process()
    if running:
        print(f"✅ REAL_SLEEP_MONEY running (PID {pid}, uptime {uptime})")
    else:
        print("❌ REAL_SLEEP_MONEY NOT RUNNING")
        print("   Start with: python3 REAL_SLEEP_MONEY.py start")
    
    # Database check
    db_issues = check_databases()
    if db_issues:
        print("\n⚠️  DATABASE ISSUES:")
        for issue in db_issues:
            print(f"   - {issue}")
    else:
        print("✅ Databases healthy")
    
    # Asset check
    asset_issues, data, products, packages = check_assets()
    print(f"\n📦 ASSETS:")
    print(f"   Data files: {data}")
    print(f"   Products:   {products}")
    print(f"   Packages:   {packages}")
    
    if asset_issues:
        print("\n⚠️  ASSET ISSUES:")
        for issue in asset_issues:
            print(f"   - {issue}")
    
    # Overall status
    all_issues = db_issues + asset_issues
    if not running:
        all_issues.append("Process not running")
    
    print()
    if all_issues:
        print("="*70)
        print(f"⚠️  {len(all_issues)} ISSUES FOUND")
        print("="*70)
        return 1
    else:
        print("="*70)
        print("✅ SYSTEM HEALTHY")
        print("="*70)
        return 0

if __name__ == "__main__":
    sys.exit(main())
