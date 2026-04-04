#!/usr/bin/env python3
"""
MONEY_LOOP.py - Persistent Revenue Generation System

This is the main money-making loop that runs 24/7.
It doesn't wait for opportunities - it CREATES them.

FOR CROPCIRCUIT SURVIVAL - ACTIVE REVENUE MODE
"""

import os
import sys
import json
import sqlite3
import subprocess
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

class MoneyLoop:
    """
    24/7 Money Generation Engine
    
    Philosophy: Don't wait for money. Go get it.
    """
    
    def __init__(self):
        self.db_path = "/home/asbelcas/rm-qpt/money_central.db"
        self.running = False
        self.cycle_count = 0
        self.daily_goal = 100.0  # $100/day target
        self.monthly_goal = 2000.0  # $2000/month
        
        os.makedirs("/home/asbelcas/rm-qpt/revenue_activities", exist_ok=True)
        os.makedirs("/home/asbelcas/rm-qpt/proposals", exist_ok=True)
        os.makedirs("/home/asbelcas/rm-qpt/outreach", exist_ok=True)
        
        self._init_database()
        self._load_state()
    
    def _init_database(self):
        """Money-focused database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Revenue targets and tracking
        c.execute('''CREATE TABLE IF NOT EXISTS revenue_goals (
            id INTEGER PRIMARY KEY,
            date TEXT,
            daily_goal REAL DEFAULT 100,
            daily_actual REAL DEFAULT 0,
            monthly_goal REAL DEFAULT 2000,
            month TEXT
        )''')
        
        # Active outreach attempts
        c.execute('''CREATE TABLE IF NOT EXISTS outreach (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            channel TEXT,
            target TEXT,
            message TEXT,
            sent BOOLEAN DEFAULT 0,
            responded BOOLEAN DEFAULT 0,
            converted BOOLEAN DEFAULT 0,
            revenue REAL DEFAULT 0
        )''')
        
        # Proposals sent
        c.execute('''CREATE TABLE IF NOT EXISTS proposals (
            id INTEGER PRIMARY KEY,
            created_at TEXT,
            client TEXT,
            project_title TEXT,
            value REAL,
            status TEXT DEFAULT 'draft',
            sent_at TEXT,
            accepted BOOLEAN DEFAULT 0,
            paid BOOLEAN DEFAULT 0
        )''')
        
        # Actual revenue (confirmed only)
        c.execute('''CREATE TABLE IF NOT EXISTS money_in (
            id INTEGER PRIMARY KEY,
            timestamp TEXT,
            source TEXT,
            amount REAL,
            method TEXT,
            related_proposal_id INTEGER,
            confirmed BOOLEAN DEFAULT 1
        )''')
        
        # Hourly activity log
        c.execute('''CREATE TABLE IF NOT EXISTS hourly_activity (
            id INTEGER PRIMARY KEY,
            hour TEXT,
            data_collected INTEGER DEFAULT 0,
            outreach_sent INTEGER DEFAULT 0,
            proposals_created INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0
        )''')
        
        # Active clients
        c.execute('''CREATE TABLE IF NOT EXISTS active_clients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            contact TEXT,
            source TEXT,
            status TEXT DEFAULT 'lead',
            last_contact TEXT,
            potential_value REAL,
            actual_paid REAL DEFAULT 0
        )''')
        
        conn.commit()
        conn.close()
    
    def _load_state(self):
        """Load current money state"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get today's revenue
        c.execute("SELECT SUM(amount) FROM money_in WHERE date(timestamp) = ?", (today,))
        self.today_revenue = c.fetchone()[0] or 0.0
        
        # Get this month's revenue
        month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        c.execute("SELECT SUM(amount) FROM money_in WHERE date(timestamp) >= ?", (month_start,))
        self.month_revenue = c.fetchone()[0] or 0.0
        
        # Get pending proposals value
        c.execute("SELECT SUM(value) FROM proposals WHERE status = 'sent' AND accepted = 0")
        self.pending_value = c.fetchone()[0] or 0.0
        
        conn.close()
    
    def log_money_activity(self, activity_type, details, value=0):
        """Log all money-making activities"""
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 💰 {activity_type}: {details}")
        
        # Also log to file
        with open("/home/asbelcas/rm-qpt/revenue_activities/money_log.txt", "a") as f:
            f.write(f"{datetime.now().isoformat()} | {activity_type} | {details} | ${value}\n")
    
    # ===================================================================
    # MONEY STREAM 1: Active Outreach (Get clients, don't wait for them)
    # ===================================================================
    
    def do_outreach(self):
        """Send outreach messages to potential clients"""
        self.log_money_activity("OUTREACH", "Scanning for outreach opportunities")
        
        # Strategy: Use collected job data to find companies hiring
        try:
            # Read latest job data
            data_files = sorted(Path("collected_data").glob("*.json"),
                              key=lambda x: x.stat().st_mtime, reverse=True)
            
            if not data_files:
                return
            
            with open(data_files[0]) as f:
                jobs = json.load(f)
            
            # Find companies that might need automation
            targets = []
            for job in jobs[:10]:  # Check 10 most recent
                title = job.get('title', '').lower()
                if any(kw in title for kw in ['data', 'automation', 'python', 'scraping', 'integration']):
                    company = job.get('company', 'Unknown')
                    targets.append({
                        'company': company,
                        'title': job.get('title'),
                        'type': 'job_posting'
                    })
            
            # Log potential targets (manual outreach for now)
            if targets:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                for target in targets[:3]:  # Top 3
                    c.execute('''INSERT OR IGNORE INTO outreach 
                        (timestamp, channel, target, message, sent)
                        VALUES (?, ?, ?, ?, ?)''',
                        (datetime.now().isoformat(),
                         'job_board_research',
                         target['company'],
                         f"Found job posting: {target['title']}",
                         0))
                
                conn.commit()
                conn.close()
                
                self.log_money_activity("TARGETS", f"Found {len(targets)} potential clients", len(targets) * 100)
                
                # Write outreach list for manual action
                outreach_file = f"/home/asbelcas/rm-qpt/outreach/targets_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
                with open(outreach_file, 'w') as f:
                    f.write("POTENTIAL CLIENTS - ACTION REQUIRED\n")
                    f.write("="*70 + "\n\n")
                    for t in targets[:5]:
                        f.write(f"Company: {t['company']}\n")
                        f.write(f"Job: {t['title']}\n")
                        f.write(f"Action: Research company, find contact, send proposal\n")
                        f.write(f"Est. Value: $200-500\n\n")
                
                return len(targets)
                
        except Exception as e:
            self.log_money_activity("ERROR", f"Outreach failed: {e}")
            return 0
    
    # ===================================================================
    # MONEY STREAM 2: Product Sales Push (Active marketing)
    # ===================================================================
    
    def push_product_sales(self):
        """Generate marketing content for products"""
        packages = list(Path("ready_to_sell").glob("*.zip"))
        
        if not packages:
            self.log_money_activity("SALES", "No products ready to sell")
            return 0
        
        # Generate marketing copy for unmarketed products
        marketed = 0
        for package in packages:
            # Check if already has marketing
            marketing_file = Path(f"/home/asbelcas/rm-qpt/outreach/{package.stem}_marketing.txt")
            if not marketing_file.exists():
                # Read the product listing
                listing_file = Path(f"/home/asbelcas/rm-qpt/ready_to_sell/{package.stem}/GUMROAD_LISTING.txt")
                if listing_file.exists():
                    with open(listing_file) as f:
                        content = f.read()
                    
                    # Generate social media posts
                    with open(marketing_file, 'w') as f:
                        f.write("SOCIAL MEDIA MARKETING COPY\n")
                        f.write("="*70 + "\n\n")
                        f.write("TWITTER/X:\n")
                        f.write("-"*70 + "\n")
                        f.write(f"Just launched: {package.stem.replace('_package', '')}\n")
                        f.write("Save hours of manual work with this Python automation.\n")
                        f.write("Perfect for freelancers and small businesses.\n")
                        f.write("Link in bio 👆\n")
                        f.write("#python #automation #productivity\n\n")
                        
                        f.write("REDDIT (r/sidehustle):\n")
                        f.write("-"*70 + "\n")
                        f.write(f"[Tool] I built {package.stem.replace('_package', '')} to help automate my workflow\n")
                        f.write("Wanted to share in case it's useful for others here.\n")
                        f.write("Happy to answer questions!\n\n")
                    
                    marketed += 1
                    self.log_money_activity("MARKETING", f"Created marketing for {package.stem}", 19)
        
        if marketed > 0:
            self.log_money_activity("SALES", f"Generated {marketed} marketing packages", marketed * 19)
        
        return marketed
    
    # ===================================================================
    # MONEY STREAM 3: Proposal Generation (Turn leads into $)
    # ===================================================================
    
    def create_proposals(self):
        """Generate proposals for active opportunities"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get uncontacted leads
        c.execute('''SELECT id, target, message FROM outreach 
            WHERE sent = 0 ORDER BY timestamp DESC LIMIT 3''')
        
        leads = c.fetchall()
        proposals_created = 0
        
        for lead_id, company, context in leads:
            # Generate proposal
            proposal_title = f"Automation Solution for {company}"
            proposal_value = 250.0  # Standard project value
            
            # Save proposal
            proposal_file = f"/home/asbelcas/rm-qpt/proposals/proposal_{company.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt"
            
            with open(proposal_file, 'w') as f:
                f.write(f"PROPOSAL: {proposal_title}\n")
                f.write("="*70 + "\n\n")
                f.write(f"To: {company}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d')}\n")
                f.write(f"Project Value: ${proposal_value}\n\n")
                f.write("CONTEXT:\n")
                f.write(f"{context}\n\n")
                f.write("PROPOSED SOLUTION:\n")
                f.write("- Custom Python automation\n")
                f.write("- Data processing and integration\n")
                f.write("- 3-day delivery\n")
                f.write("- 30-day support\n\n")
                f.write("NEXT STEPS:\n")
                f.write("Reply to discuss requirements\n")
            
            # Update database
            c.execute('''INSERT INTO proposals 
                (created_at, client, project_title, value, status)
                VALUES (?, ?, ?, ?, ?)''',
                (datetime.now().isoformat(), company, proposal_title, proposal_value, 'draft'))
            
            c.execute('UPDATE outreach SET sent = 1 WHERE id = ?', (lead_id,))
            
            proposals_created += 1
            self.log_money_activity("PROPOSAL", f"Created proposal for {company}", proposal_value)
        
        conn.commit()
        conn.close()
        
        if proposals_created > 0:
            self.log_money_activity("PROPOSALS", f"Created {proposals_created} proposals", proposals_created * 250)
        
        return proposals_created
    
    # ===================================================================
    # MONEY STREAM 4: Track and Report Revenue
    # ===================================================================
    
    def update_revenue_tracking(self):
        """Update all revenue metrics"""
        self._load_state()
        
        # Calculate progress
        daily_progress = (self.today_revenue / self.daily_goal) * 100
        monthly_progress = (self.month_revenue / self.monthly_goal) * 100
        
        # Log status
        self.log_money_activity("REVENUE", 
            f"Today: ${self.today_revenue:.2f}/{self.daily_goal:.0f} ({daily_progress:.1f}%) | " +
            f"Month: ${self.month_revenue:.2f}/{self.monthly_goal:.0f} ({monthly_progress:.1f}%) | " +
            f"Pending: ${self.pending_value:.2f}")
        
        # Check if we're behind
        hour = datetime.now().hour
        expected_by_now = (hour / 24) * self.daily_goal
        
        if self.today_revenue < expected_by_now * 0.5:
            self.log_money_activity("ALERT", f"Behind target! Expected ${expected_by_now:.0f}, have ${self.today_revenue:.2f}")
            return "BEHIND"
        elif self.today_revenue >= self.daily_goal:
            self.log_money_activity("SUCCESS", f"Daily goal reached! ${self.today_revenue:.2f}")
            return "GOAL_MET"
        else:
            return "ON_TRACK"
    
    # ===================================================================
    # MAIN MONEY LOOP
    # ===================================================================
    
    def money_cycle(self):
        """One cycle of money-making activities"""
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        print(f"\n{'='*70}")
        print(f"💰 MONEY CYCLE #{self.cycle_count} - {cycle_start.strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        results = {
            'outreach': 0,
            'marketing': 0,
            'proposals': 0,
            'status': ''
        }
        
        # 1. Check current revenue status
        results['status'] = self.update_revenue_tracking()
        
        # 2. If behind or no revenue, push harder
        if results['status'] in ['BEHIND', 'ON_TRACK'] or self.today_revenue == 0:
            # Do outreach
            results['outreach'] = self.do_outreach()
            
            # Push product sales
            results['marketing'] = self.push_product_sales()
            
            # Create proposals
            results['proposals'] = self.create_proposals()
        
        # 3. Log hourly activity
        hour = datetime.now().strftime('%Y-%m-%d_%H')
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT OR REPLACE INTO hourly_activity 
            (hour, outreach_sent, proposals_created, revenue_generated)
            VALUES (?, COALESCE((SELECT outreach_sent FROM hourly_activity WHERE hour = ?), 0) + ?,
                          COALESCE((SELECT proposals_created FROM hourly_activity WHERE hour = ?), 0) + ?,
                          ?)''',
            (hour, hour, results['outreach'], hour, results['proposals'], self.today_revenue))
        
        conn.commit()
        conn.close()
        
        # Summary
        print(f"\n📊 CYCLE RESULTS:")
        print(f"   Outreach targets: {results['outreach']}")
        print(f"   Marketing pieces: {results['marketing']}")
        print(f"   Proposals created: {results['proposals']}")
        print(f"   Status: {results['status']}")
        print(f"   Today's revenue: ${self.today_revenue:.2f}")
        
        cycle_time = (datetime.now() - cycle_start).total_seconds()
        print(f"\n⏱️  Cycle time: {cycle_time:.1f}s")
        print(f"   Next cycle in 15 minutes...")
        
        return results
    
    def run(self):
        """Main money loop - runs forever"""
        print("\n" + "="*70)
        print("  💰 MONEY_LOOP - Persistent Revenue Generation")
        print("  Target: $100/day | $2000/month")
        print("="*70)
        print("\n  This system works FOR money, not just waits for it.")
        print("  Starting 24/7 revenue generation...\n")
        
        self.running = True
        
        try:
            while self.running:
                self.money_cycle()
                
                # Sleep 15 minutes between cycles
                for i in range(900):  # 15 minutes
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n\n💰 Money loop stopped.")
            self.running = False
    
    def show_dashboard(self):
        """Show money dashboard"""
        self._load_state()
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get stats
        c.execute("SELECT COUNT(*), SUM(CASE WHEN sent THEN 1 ELSE 0 END) FROM outreach")
        total_outreach, sent_outreach = c.fetchone()
        
        c.execute("SELECT COUNT(*), SUM(CASE WHEN accepted THEN 1 ELSE 0 END) FROM proposals")
        total_proposals, accepted_proposals = c.fetchone()
        
        conn.close()
        
        print("\n" + "="*70)
        print("💰 MONEY DASHBOARD")
        print("="*70)
        print(f"\n📈 REVENUE:")
        print(f"   Today:     ${self.today_revenue:.2f} / ${self.daily_goal:.0f}")
        print(f"   This Month: ${self.month_revenue:.2f} / ${self.monthly_goal:.0f}")
        print(f"   Pending:   ${self.pending_value:.2f}")
        
        print(f"\n🎯 ACTIVITY:")
        print(f"   Outreach:     {sent_outreach or 0} / {total_outreach or 0}")
        print(f"   Proposals:    {accepted_proposals or 0} / {total_proposals or 0}")
        
        # Calculate hourly rate needed
        hours_left = 24 - datetime.now().hour
        if hours_left > 0 and self.today_revenue < self.daily_goal:
            needed = (self.daily_goal - self.today_revenue) / hours_left
            print(f"\n⚡ To hit daily goal: Need ${needed:.2f}/hour for next {hours_left} hours")
        
        print("="*70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Money Loop - Persistent Revenue")
    parser.add_argument('action', choices=['run', 'dashboard', 'status'], nargs='?', default='dashboard')
    
    args = parser.parse_args()
    
    loop = MoneyLoop()
    
    if args.action == 'run':
        loop.run()
    elif args.action == 'status':
        loop.update_revenue_tracking()
    else:
        loop.show_dashboard()

if __name__ == "__main__":
    main()
