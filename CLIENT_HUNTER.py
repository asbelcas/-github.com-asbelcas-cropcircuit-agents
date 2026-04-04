#!/usr/bin/env python3
"""
CLIENT_HUNTER.py - Active Client Acquisition

Don't wait for clients to find you. Hunt them down.

Strategies:
1. Monitor job boards for new postings (react fast)
2. Extract contact info from collected data
3. Generate targeted proposals
4. Track follow-ups religiously
"""

import os
import sys
import json
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

class ClientHunter:
    """
    Actively hunts for clients and converts them into paying work.
    """
    
    def __init__(self):
        self.db_path = "/home/asbelcas/rm-qpt/money_central.db"
        self.hunt_log = "/home/asbelcas/rm-qpt/outreach/hunt_log.txt"
        self._init_tables()
    
    def _init_tables(self):
        """Ensure hunter tables exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS hunt_targets (
            id INTEGER PRIMARY KEY,
            discovered_at TEXT,
            source TEXT,
            company TEXT,
            contact_email TEXT,
            job_title TEXT,
            job_url TEXT,
            skills_needed TEXT,
            budget_hint TEXT,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'new',
            contacted_at TEXT,
            proposal_sent BOOLEAN DEFAULT 0,
            responded BOOLEAN DEFAULT 0,
            notes TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS hunt_activity (
            id INTEGER PRIMARY KEY,
            date TEXT,
            targets_found INTEGER DEFAULT 0,
            contacted INTEGER DEFAULT 0,
            proposals INTEGER DEFAULT 0,
            responses INTEGER DEFAULT 0
        )''')
        
        conn.commit()
        conn.close()
    
    def log_hunt(self, message):
        """Log hunting activity"""
        ts = datetime.now().strftime('%H:%M:%S')
        print(f"[{ts}] 🎯 {message}")
        
        with open(self.hunt_log, "a") as f:
            f.write(f"{datetime.now().isoformat()} | {message}\n")
    
    def scan_for_targets(self):
        """
        Scan collected data for high-value targets.
        Focus on companies posting jobs we can do.
        """
        self.log_hunt("Scanning for targets...")
        
        # Read recent job data
        data_files = sorted(Path("collected_data").glob("*.json"),
                          key=lambda x: x.stat().st_mtime, reverse=True)[:3]
        
        targets_found = 0
        
        for data_file in data_files:
            try:
                with open(data_file) as f:
                    jobs = json.load(f)
                
                for job in jobs:
                    title = job.get('title', '').lower()
                    
                    # Score the opportunity (title + description)
                    score = 0
                    keywords = {
                        'python': 2,
                        'automation': 3,
                        'script': 2,
                        'scraping': 3,
                        'data': 1,
                        'api': 2,
                        'integration': 3,
                        'bot': 2,
                        'developer': 1,
                        'engineer': 1,
                        'software': 1
                    }
                    
                    text_to_check = (title + " " + job.get('description', '')).lower()
                    matched_skills = []
                    
                    for kw, points in keywords.items():
                        if kw in text_to_check:
                            score += points
                            matched_skills.append(kw)
                    
                    # Only track high-value targets
                    if score >= 3:
                        company = job.get('company', 'Unknown')
                        
                        # Check if already tracked
                        conn = sqlite3.connect(self.db_path)
                        c = conn.cursor()
                        
                        c.execute("SELECT COUNT(*) FROM hunt_targets WHERE company = ? AND job_title = ?",
                            (company, job.get('title')))
                        
                        if c.fetchone()[0] == 0:
                            # New target
                            c.execute('''INSERT INTO hunt_targets
                                (discovered_at, source, company, job_title, job_url, 
                                 skills_needed, priority, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                                (datetime.now().isoformat(),
                                 data_file.stem,
                                 company,
                                 job.get('title'),
                                 job.get('link', ''),
                                 ', '.join(matched_skills),
                                 min(score, 10),
                                 'new'))
                            
                            targets_found += 1
                            self.log_hunt(f"NEW TARGET: {company} - {job.get('title')[:40]}... (score: {score})")
                        
                        conn.commit()
                        conn.close()
                        
            except Exception as e:
                self.log_hunt(f"Error scanning {data_file}: {e}")
        
        # Log activity
        if targets_found > 0:
            self._log_activity(targets_found=targets_found)
        
        return targets_found
    
    def prioritize_targets(self):
        """Sort targets by priority and readiness"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT id, company, job_title, priority, status 
            FROM hunt_targets 
            WHERE status = 'new'
            ORDER BY priority DESC, discovered_at DESC
            LIMIT 10''')
        
        targets = c.fetchall()
        conn.close()
        
        return targets
    
    def generate_approach(self, target_id):
        """
        Generate approach strategy for a target.
        Creates email draft and proposal outline.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''SELECT company, job_title, job_url, skills_needed 
            FROM hunt_targets WHERE id = ?''', (target_id,))
        
        target = c.fetchone()
        if not target:
            conn.close()
            return None
        
        company, title, url, skills = target
        
        # Generate approach files
        approach_dir = Path(f"/home/asbelcas/rm-qpt/outreach/approaches/{company.replace(' ', '_')}")
        approach_dir.mkdir(parents=True, exist_ok=True)
        
        # Email draft
        email_file = approach_dir / "email_draft.txt"
        with open(email_file, 'w') as f:
            f.write(f"Subject: Re: {title}\n\n")
            f.write(f"Hi {company} Team,\n\n")
            f.write(f"I saw your posting for {title} and wanted to reach out.\n\n")
            f.write("I specialize in Python automation and can help with:\n")
            if skills:
                for skill in skills.split(',')[:3]:
                    f.write(f"- {skill.strip().title()}\n")
            f.write("\n")
            f.write("I've built similar solutions for other clients and can deliver quickly.\n\n")
            f.write("Would you be open to a quick call to discuss your needs?\n\n")
            f.write("Best regards,\n")
            f.write("CropCircuit Automation\n\n")
            f.write(f"Reference: {url}\n")
        
        # Proposal outline
        proposal_file = approach_dir / "proposal_outline.txt"
        with open(proposal_file, 'w') as f:
            f.write(f"PROPOSAL OUTLINE: {company}\n")
            f.write("="*70 + "\n\n")
            f.write(f"Project: {title}\n")
            f.write("Services:\n")
            f.write("- Custom Python development\n")
            f.write("- Automation solution\n")
            f.write("- Testing and delivery\n")
            f.write("- 30-day support\n\n")
            f.write("Timeline: 3-5 days\n")
            f.write("Investment: $250-500 (depending on scope)\n\n")
            f.write("Next: Send email, wait for response, customize proposal\n")
        
        # Update target
        c.execute('''UPDATE hunt_targets 
            SET status = 'approach_ready', notes = ?
            WHERE id = ?''',
            (f"Approach ready in {approach_dir}", target_id))
        
        conn.commit()
        conn.close()
        
        self.log_hunt(f"Approach ready for {company}")
        return approach_dir
    
    def execute_hunt(self):
        """
        Main hunting routine - find targets and prepare approaches.
        """
        self.log_hunt("="*70)
        self.log_hunt("HUNT EXECUTION STARTED")
        self.log_hunt("="*70)
        
        # 1. Find new targets
        new_targets = self.scan_for_targets()
        
        # 2. Prioritize existing targets
        targets = self.prioritize_targets()
        
        # 3. Generate approaches for top targets
        approaches_ready = 0
        for target in targets[:3]:  # Top 3
            target_id = target[0]
            company = target[1]
            
            approach = self.generate_approach(target_id)
            if approach:
                approaches_ready += 1
        
        # 4. Summary
        self.log_hunt("-"*70)
        self.log_hunt(f"HUNT COMPLETE: {new_targets} new targets, {approaches_ready} approaches ready")
        self.log_hunt("-"*70)
        
        # Update activity
        self._log_activity(approaches=approaches_ready)
        
        return {
            'new_targets': new_targets,
            'approaches_ready': approaches_ready,
            'total_pending': len(targets)
        }
    
    def _log_activity(self, targets_found=0, contacted=0, proposals=0, responses=0, approaches=0):
        """Log daily hunting activity"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO hunt_activity (date, targets_found, contacted, proposals, responses)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                targets_found = targets_found + ?,
                contacted = contacted + ?,
                proposals = proposals + ?,
                responses = responses + ?''',
            (today, targets_found, contacted, proposals + approaches, responses,
             targets_found, contacted, proposals + approaches, responses))
        
        conn.commit()
        conn.close()
    
    def show_hunt_board(self):
        """Display hunting dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Targets by status
        c.execute('''SELECT status, COUNT(*), AVG(priority) 
            FROM hunt_targets GROUP BY status''')
        status_counts = c.fetchall()
        
        # High priority targets (new)
        c.execute('''SELECT company, job_title, priority 
            FROM hunt_targets WHERE status = 'new' 
            ORDER BY priority DESC LIMIT 5''')
        top_targets = c.fetchall()
        
        # Today's activity
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT targets_found, contacted, proposals 
            FROM hunt_activity WHERE date = ?''', (today,))
        today_stats = c.fetchone()
        
        conn.close()
        
        print("\n" + "="*70)
        print("🎯 HUNT BOARD")
        print("="*70)
        
        print("\n📊 TARGETS BY STATUS:")
        for status, count, avg_priority in status_counts:
            print(f"   {status:15} {count:3} (avg priority: {avg_priority:.1f})")
        
        print("\n🎯 TOP PRIORITY TARGETS:")
        for company, title, priority in top_targets:
            print(f"   [{priority}/10] {company}: {title[:40]}...")
        
        if today_stats:
            print(f"\n📈 TODAY'S ACTIVITY:")
            print(f"   Targets found: {today_stats[0]}")
            print(f"   Contacted: {today_stats[1]}")
            print(f"   Proposals: {today_stats[2]}")
        
        print("="*70)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Client Hunter - Active Acquisition")
    parser.add_argument('action', choices=['hunt', 'board', 'targets'], nargs='?', default='board')
    
    args = parser.parse_args()
    
    hunter = ClientHunter()
    
    if args.action == 'hunt':
        hunter.execute_hunt()
    elif args.action == 'targets':
        targets = hunter.prioritize_targets()
        print(f"\nTop {len(targets)} targets:")
        for t in targets:
            print(f"  [{t[3]}/10] {t[1]}: {t[2][:40]}")
    else:
        hunter.show_hunt_board()

if __name__ == "__main__":
    main()
