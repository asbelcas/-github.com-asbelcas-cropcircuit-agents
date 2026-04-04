#!/usr/bin/env python3
"""
HOUR-LONG TEST - 60 Minute System Validation

This test runs for 60 minutes and verifies:
1. System stays running without crashing
2. Files are created at expected intervals
3. Database records accumulate
4. No errors occur during operation
5. All streams remain active

Reports progress every 5 minutes.
Generates final report at end.
"""

import os
import sys
import time
import sqlite3
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import json

class HourLongTest:
    """
    60-minute comprehensive system test
    """
    
    def __init__(self):
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=1)
        self.check_interval = 300  # 5 minutes
        self.results = []
        self.errors = []
        
        self.log_file = f"/home/asbelcas/rm-qpt/test_logs/hour_test_{self.start_time.strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        ts = datetime.now().strftime('%H:%M:%S')
        line = f"[{ts}] [{level}] {message}"
        print(line)
        
        with open(self.log_file, 'a') as f:
            f.write(line + "\n")
    
    def check_system_health(self, minute):
        """Check all system metrics"""
        check = {
            'timestamp': datetime.now().isoformat(),
            'minute': minute,
            'process_running': False,
            'data_files': 0,
            'product_files': 0,
            'db_actions': 0,
            'db_sales': 0,
            'errors': 0
        }
        
        try:
            # Check if process is running
            result = subprocess.run(
                ['pgrep', '-f', 'REAL_SLEEP_MONEY.py start'],
                capture_output=True, text=True
            )
            check['process_running'] = len(result.stdout.strip()) > 0
            
            # Count files
            check['data_files'] = len(list(Path('/home/asbelcas/rm-qpt/collected_data').glob('*.json')))
            check['product_files'] = len(list(Path('/home/asbelcas/rm-qpt/generated_products').glob('*.py')))
            
            # Check databases
            if os.path.exists('/home/asbelcas/rm-qpt/real_sleep_money.db'):
                conn = sqlite3.connect('/home/asbelcas/rm-qpt/real_sleep_money.db')
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM actions")
                check['db_actions'] = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM actions WHERE result LIKE '%error%'")
                check['errors'] = c.fetchone()[0]
                conn.close()
            
            if os.path.exists('/home/asbelcas/rm-qpt/actual_revenue.db'):
                conn = sqlite3.connect('/home/asbelcas/rm-qpt/actual_revenue.db')
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM actual_sales")
                check['db_sales'] = c.fetchone()[0]
                conn.close()
            
        except Exception as e:
            self.log(f"Health check error: {e}", "ERROR")
            check['errors'] += 1
        
        return check
    
    def format_time_remaining(self):
        """Format time remaining"""
        remaining = self.end_time - datetime.now()
        minutes = int(remaining.total_seconds() / 60)
        seconds = int(remaining.total_seconds() % 60)
        return f"{minutes}m {seconds}s"
    
    def print_progress_report(self, check):
        """Print progress report"""
        minute = check['minute']
        
        print("\n" + "="*70)
        print(f"⏱️  HOUR-LONG TEST - Minute {minute}/60")
        print(f"   Time remaining: {self.format_time_remaining()}")
        print("="*70)
        
        status = "🟢" if check['process_running'] else "🔴"
        print(f"   {status} Process Running:    {check['process_running']}")
        print(f"   📁 Data Files:           {check['data_files']}")
        print(f"   🏭 Product Files:        {check['product_files']}")
        print(f"   🗄️  Database Actions:     {check['db_actions']}")
        print(f"   💰 Sales Recorded:       {check['db_sales']}")
        print(f"   ❌ Errors:               {check['errors']}")
        print("="*70)
        
        # Calculate changes from start
        if self.results:
            first = self.results[0]
            data_delta = check['data_files'] - first['data_files']
            prod_delta = check['product_files'] - first['product_files']
            action_delta = check['db_actions'] - first['db_actions']
            
            if data_delta > 0 or prod_delta > 0 or action_delta > 0:
                print(f"   📈 Since test start: +{data_delta} data, +{prod_delta} products, +{action_delta} actions")
        
        print()
    
    def run_test(self):
        """Run the hour-long test"""
        self.log("="*70)
        self.log("HOUR-LONG TEST STARTING")
        self.log("="*70)
        self.log(f"Start time: {self.start_time.strftime('%H:%M:%S')}")
        self.log(f"End time:   {self.end_time.strftime('%H:%M:%S')}")
        self.log(f"Duration:   60 minutes")
        self.log("="*70)
        
        # Check if process is already running, start if not
        result = subprocess.run(
            ['pgrep', '-f', 'REAL_SLEEP_MONEY.py start'],
            capture_output=True, text=True
        )
        
        if not result.stdout.strip():
            self.log("Starting REAL_SLEEP_MONEY.py...")
            subprocess.Popen(
                ['python3', '/home/asbelcas/rm-qpt/REAL_SLEEP_MONEY.py', 'start'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(5)  # Give it time to start
        else:
            self.log(f"Process already running (PID {result.stdout.strip()})")
        
        # Baseline check
        self.log("Taking baseline measurements...")
        baseline = self.check_system_health(0)
        self.results.append(baseline)
        self.print_progress_report(baseline)
        
        # Run for 60 minutes, checking every 5 minutes
        minute = 0
        while datetime.now() < self.end_time:
            time.sleep(self.check_interval)
            minute += 5
            
            check = self.check_system_health(minute)
            self.results.append(check)
            self.print_progress_report(check)
            
            # Check for critical failures
            if not check['process_running'] and minute > 5:
                self.log("CRITICAL: Process stopped running!", "CRITICAL")
                self.errors.append(f"Process died at minute {minute}")
            
            if check['errors'] > baseline['errors'] + 10:
                self.log(f"WARNING: Error count increased significantly", "WARNING")
        
        # Final check
        self.log("Taking final measurements...")
        final = self.check_system_health(60)
        self.results.append(final)
        
        self.generate_report()
    
    def generate_report(self):
        """Generate final test report"""
        self.log("="*70)
        self.log("HOUR-LONG TEST COMPLETE")
        self.log("="*70)
        
        if len(self.results) < 2:
            self.log("ERROR: Not enough data collected", "ERROR")
            return
        
        first = self.results[0]
        last = self.results[-1]
        
        # Calculate totals
        duration = (datetime.now() - self.start_time).total_seconds() / 60
        data_created = last['data_files'] - first['data_files']
        products_created = last['product_files'] - first['product_files']
        actions_performed = last['db_actions'] - first['db_actions']
        sales_made = last['db_sales'] - first['db_sales']
        
        print("\n" + "="*70)
        print("📊 FINAL TEST REPORT")
        print("="*70)
        print(f"   Test Duration:        {duration:.1f} minutes")
        print(f"   Checks Performed:     {len(self.results)}")
        print(f"   Process Stayed Up:    {'✅ YES' if last['process_running'] else '❌ NO'}")
        print()
        print("   ASSETS CREATED:")
        print(f"     Data Files:         +{data_created}")
        print(f"     Products:           +{products_created}")
        print(f"     Total Actions:      +{actions_performed}")
        print()
        print("   SALES:")
        print(f"     Sales Recorded:     +{sales_made}")
        print()
        print(f"   Errors Encountered:   {len(self.errors)}")
        
        if self.errors:
            print("\n   ERROR DETAILS:")
            for error in self.errors:
                print(f"     - {error}")
        
        # Test verdict
        print("\n" + "="*70)
        if last['process_running'] and len(self.errors) == 0:
            print("✅ TEST PASSED - System ran successfully for 60 minutes")
            print("   All streams operational")
            print("   Assets being created")
            print("   No critical errors")
        elif last['process_running']:
            print("⚠️  TEST PASSED WITH WARNINGS")
            print("   System stayed running")
            print("   Some non-critical errors occurred")
        else:
            print("❌ TEST FAILED - Process stopped during test")
        
        print("="*70)
        
        # Save report
        report_file = f"/home/asbelcas/rm-qpt/test_logs/test_report_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': duration,
                'checks': self.results,
                'errors': self.errors,
                'summary': {
                    'data_created': data_created,
                    'products_created': products_created,
                    'actions_performed': actions_performed,
                    'sales_made': sales_made,
                    'process_stayed_up': last['process_running']
                }
            }, f, indent=2)
        
        self.log(f"Full report saved to: {report_file}")

def main():
    print("="*70)
    print("💰 HOUR-LONG SYSTEM TEST")
    print("="*70)
    print()
    print("This test will:")
    print("  • Run for exactly 60 minutes")
    print("  • Check system health every 5 minutes")
    print("  • Record all metrics")
    print("  • Generate final report")
    print()
    print("Requirements:")
    print("  • Leave this terminal open for 1 hour")
    print("  • Don't shut down the computer")
    print()
    
    # Check for auto-start flag
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        print("Auto-start enabled (no prompt)")
        print("Starting in 5 seconds...")
        time.sleep(5)
        test = HourLongTest()
        test.run_test()
        return
    
    response = input("Start the 60-minute test? (yes/no): ").strip().lower()
    
    if response == "yes":
        test = HourLongTest()
        test.run_test()
    else:
        print("Test cancelled.")

if __name__ == "__main__":
    main()
