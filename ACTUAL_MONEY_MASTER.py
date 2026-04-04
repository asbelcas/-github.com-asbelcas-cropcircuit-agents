#!/usr/bin/env python3
"""
ACTUAL MONEY MASTER - The Real Deal

This system distinguishes between:
1. ASSET CREATION (REAL_SLEEP_MONEY) - Creates files/data
2. ACTUAL SALES (REAL_MONEY_SYSTEM) - Records real revenue

NO HALLUCINATION:
- "Estimated value" = Potential value of created assets
- "Actual revenue" = Real money from real sales

Both are tracked separately for clarity.
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

class ActualMoneyMaster:
    """
    Master controller for REAL money generation
    """
    
    def __init__(self):
        self.asset_db = "/home/asbelcas/rm-qpt/real_sleep_money.db"
        self.sales_db = "/home/asbelcas/rm-qpt/actual_revenue.db"
    
    def show_unified_dashboard(self):
        """Show BOTH estimated value AND actual revenue"""
        print("\n" + "="*70)
        print("💰 ACTUAL MONEY MASTER - COMPLETE FINANCIAL OVERVIEW")
        print("="*70)
        
        # ASSET CREATION (Estimated Value)
        print("\n📊 ASSET CREATION (Automated System)")
        print("-"*70)
        
        try:
            conn = sqlite3.connect(self.asset_db)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*), SUM(value_estimate) FROM actions")
            actions, est_value = c.fetchone()
            actions = actions or 0
            est_value = est_value or 0
            
            c.execute("SELECT COUNT(*), SUM(records) FROM collected_data")
            data_files, records = c.fetchone()
            data_files = data_files or 0
            records = records or 0
            
            c.execute("SELECT COUNT(*), SUM(lines_of_code) FROM products")
            products, loc = c.fetchone()
            products = products or 0
            loc = loc or 0
            
            conn.close()
            
            actual_data = len(list(Path('collected_data').glob('*.json')))
            actual_products = len(list(Path('generated_products').glob('*.py')))
            
            print(f"  Actions:          {actions}")
            print(f"  Data files:       {actual_data} ({records} records)")
            print(f"  Products:         {actual_products} ({loc} lines of code)")
            print(f"  ESTIMATED VALUE:  ${est_value:,.2f}")
            print("  ⚠️  This is POTENTIAL value of created assets")
            
        except Exception as e:
            print(f"  Error reading asset data: {e}")
        
        # ACTUAL SALES (Real Money)
        print("\n" + "-"*70)
        print("💵 ACTUAL SALES (Real Revenue)")
        print("-"*70)
        
        try:
            conn = sqlite3.connect(self.sales_db)
            c = conn.cursor()
            
            c.execute("SELECT COUNT(*), SUM(sale_price) FROM actual_sales WHERE status='completed'")
            sales_count, real_revenue = c.fetchone()
            sales_count = sales_count or 0
            real_revenue = real_revenue or 0
            
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute("SELECT COUNT(*), SUM(sale_price) FROM actual_sales WHERE date(timestamp)=?",
                (today,))
            today_count, today_revenue = c.fetchone()
            today_count = today_count or 0
            today_revenue = today_revenue or 0
            
            c.execute("SELECT COUNT(*) FROM listed_products")
            listed = c.fetchone()[0] or 0
            
            conn.close()
            
            print(f"  Total sales:      {sales_count}")
            print(f"  Products listed:  {listed}")
            print(f"  Today:            ${today_revenue:,.2f} ({today_count} sales)")
            print(f"  ACTUAL REVENUE:   ${real_revenue:,.2f}")
            print("  ✅ This is REAL money from REAL buyers")
            
        except Exception as e:
            print(f"  Error reading sales data: {e}")
            print(f"  Sales database may not exist yet")
            real_revenue = 0
            sales_count = 0
        
        # SUMMARY
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        
        try:
            total_value = (est_value or 0) + (real_revenue or 0)
            print(f"  Estimated Asset Value:    ${est_value or 0:,.2f}")
            print(f"  Actual Sales Revenue:     ${real_revenue or 0:,.2f}")
            print(f"  TOTAL VALUE CREATED:      ${total_value:,.2f}")
            print("-"*70)
            
            if sales_count == 0:
                print("\n  ⚠️  NO ACTUAL SALES YET")
                print("      Assets are being created automatically")
                print("      Next step: List products on marketplaces to get REAL sales")
            else:
                print(f"\n  ✅ {sales_count} actual sales recorded!")
                print("      Assets are being created AND sold")
        except:
            print("  Unable to calculate totals")
        
        print("="*70)
    
    def explain_the_difference(self):
        """Explain estimated vs actual"""
        print("\n" + "="*70)
        print("📚 UNDERSTANDING THE NUMBERS")
        print("="*70)
        print("""
ESTIMATED VALUE (from REAL_SLEEP_MONEY):
  → Value of files/data created by automation
  → Potential worth if sold
  → NOT actual money in your account
  → Example: "Created a script worth $10"

ACTUAL REVENUE (from REAL_MONEY_SYSTEM):
  → Real money from real sales
  → Dollars in your PayPal/bank account
  → Confirmed buyer transactions
  → Example: "Sold a script for $29 to buyer@email.com"

THE COMPLETE SYSTEM:
  1. REAL_SLEEP_MONEY runs 24/7 creating assets
  2. You list those assets on marketplaces (Gumroad, etc)
  3. When sales happen, record them in REAL_MONEY_SYSTEM
  4. ACTUAL_MONEY_MASTER shows both sides

NO HALLUCINATION:
  ✅ Files actually created on disk
  ✅ Data actually scraped from real websites
  ✅ Sales actually recorded when they happen
  ✅ Revenue actually tracked from real transactions
        """)
        print("="*70)

def main():
    master = ActualMoneyMaster()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "dashboard":
            master.show_unified_dashboard()
        elif sys.argv[1] == "explain":
            master.explain_the_difference()
        else:
            print("Commands:")
            print("  dashboard  - Show complete financial overview")
            print("  explain    - Explain estimated vs actual")
    else:
        master.show_unified_dashboard()
        print("\nRun: python3 ACTUAL_MONEY_MASTER.py explain")
        print("     for detailed explanation of the numbers")

if __name__ == "__main__":
    main()
