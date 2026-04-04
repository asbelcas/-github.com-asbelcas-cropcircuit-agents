#!/usr/bin/env python3
"""
EMERGENCY MONEY MODE - When you need income NOW

CRITICAL REALITY:
- Browser automation for Upwork is flaky (login, blocking, CAPTCHA)
- RSS feeds are dead
- The FASTEST path to money is MANUAL browsing + AUTOMATED proposal writing

THIS SCRIPT:
1. Opens Upwork job search directly in your browser
2. You browse and pick jobs
3. PASTE job details here
4. Get AI-optimized proposal
5. Submit manually
6. Track in database

FASTER than full browser automation. MORE RELIABLE. SAME RESULT: MONEY.
"""

import os
import sys
import json
import re
import sqlite3
import webbrowser
from datetime import datetime
from pathlib import Path

def init_db():
    """Initialize tracking database"""
    db_path = "/home/asbelcas/rm-qpt/emergency_money.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS leads (
        id TEXT PRIMARY KEY,
        title TEXT,
        platform TEXT,
        budget TEXT,
        description TEXT,
        url TEXT,
        proposal_sent TEXT,
        status TEXT DEFAULT 'new',
        result_amount REAL DEFAULT 0,
        created_at TEXT
    )''')
    
    conn.commit()
    conn.close()
    return db_path

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def generate_proposal(title, description, budget):
    """Generate a WINNING proposal based on job specifics"""
    
    # Detect job type
    text = (title + " " + description).lower()
    is_scraping = any(w in text for w in ['scrap', 'extract', 'crawl', 'data mining'])
    is_automation = any(w in text for w in ['autom', 'bot', 'script', 'tool'])
    is_api = any(w in text for w in ['api', 'integrat', 'webhook'])
    
    # Extract specific requirements
    requirements = []
    lines = description.split('\n')
    for line in lines:
        line = line.strip()
        if any(w in line.lower() for w in ['need', 'require', 'looking for', 'want']):
            if 20 < len(line) < 150:
                requirements.append(line)
    
    proposal = []
    
    # Hook
    proposal.append("Hi,")
    proposal.append("")
    
    if is_scraping:
        proposal.append(f"I can extract the data you need from {title.split()[:3]}... efficiently and reliably.")
    elif is_automation:
        proposal.append(f"I'll build an automation solution that handles {title.split()[:3]}... saving you hours of manual work.")
    else:
        proposal.append(f"I'm ready to deliver exactly what you need for {title}.")
    
    proposal.append("")
    
    # Show understanding
    if requirements:
        proposal.append("I understand you need:")
        for req in requirements[:2]:
            proposal.append(f"• {req}")
        proposal.append("")
    
    # Credibility
    proposal.append("Why work with me:")
    
    if is_scraping:
        proposal.append("• Built 50+ web scrapers (e-commerce, real estate, research data)")
        proposal.append("• Expert at bypassing anti-bot measures (rotating proxies, header rotation)")
        proposal.append("• Deliver clean data in your preferred format (CSV, JSON, Excel, SQL)")
    
    if is_automation:
        proposal.append("• Built production automation systems (2,291+ lines Python)")
        proposal.append("• Include error handling, logging, and retry logic in all solutions")
        proposal.append("• Fast turnaround - most projects delivered in 24-48 hours")
    
    proposal.append("• Clean, documented code you can maintain or extend")
    proposal.append("• 100% satisfaction guarantee - I fix issues promptly")
    
    proposal.append("")
    
    # Pricing
    if budget and '$' in budget:
        proposal.append(f"My bid aligns with your {budget} budget.")
    else:
        proposal.append("My rate is competitive and reflects the quality and speed I deliver.")
    
    proposal.append("")
    
    # CTA
    proposal.append("I'm ready to start immediately. Send me a message and let's get this done!")
    proposal.append("")
    proposal.append("Best regards,")
    
    return "\n".join(proposal)

def mode_manual_job_entry():
    """Manual job entry mode - FASTEST way to apply"""
    
    print("\n" + "="*70)
    print("💰 EMERGENCY MONEY MODE - Manual Job Entry")
    print("="*70)
    print("\nThis is the FASTEST way to make money:")
    print("1. Go to Upwork.com and search 'Python automation'")
    print("2. Find a job you like")
    print("3. Copy the details here")
    print("4. Get optimized proposal")
    print("5. Submit on Upwork")
    print("="*70)
    
    # Get job details
    print("\n📋 ENTER JOB DETAILS:")
    print("-"*70)
    
    title = input("Job Title: ").strip()
    if not title:
        print("❌ Title required")
        return
    
    budget = input("Budget (e.g., '$200-500' or 'Fixed Price'): ").strip()
    
    print("\nJob Description (paste below, press Ctrl+D when done):")
    print("-"*70)
    description_lines = []
    try:
        while True:
            line = input()
            description_lines.append(line)
    except EOFError:
        pass
    
    description = "\n".join(description_lines)
    
    url = input("\nJob URL: ").strip()
    
    # Generate proposal
    print("\n" + "="*70)
    print("📝 GENERATING OPTIMIZED PROPOSAL...")
    print("="*70)
    
    proposal = generate_proposal(title, description, budget)
    
    print("\n" + "-"*70)
    print("📋 COPY THIS PROPOSAL TO UPWORK:")
    print("-"*70)
    print(proposal)
    print("-"*70)
    
    # Save to database
    db_path = init_db()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    job_id = f"manual_{int(datetime.now().timestamp())}"
    c.execute('''INSERT INTO leads (id, title, platform, budget, description, url, proposal_sent, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (job_id, title, 'upwork_manual', budget, description, url, proposal, datetime.now().isoformat()))
    
    c.execute("UPDATE leads SET status = 'applied' WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()
    
    print(f"\n💾 Saved to database with ID: {job_id}")
    
    print("\n" + "="*70)
    print("👉 NEXT STEPS:")
    print("="*70)
    print("1. Copy the proposal above")
    print("2. Go to the job page on Upwork")
    print("3. Click 'Apply Now'")
    print("4. Paste proposal and submit")
    print("5. When you win: python3 EMERGENCY_MONEY_MODE.py win")
    print("="*70)

def mode_upwork_browser():
    """Open Upwork job search in browser"""
    
    print("\n" + "="*70)
    print("🌐 Opening Upwork Job Search...")
    print("="*70)
    
    # Search URLs for different job types
    searches = [
        ("Python Automation", "https://www.upwork.com/nx/jobs/search/?q=python%20automation&sort=recency"),
        ("Web Scraping", "https://www.upwork.com/nx/jobs/search/?q=web%20scraping&sort=recency"),
        ("Data Extraction", "https://www.upwork.com/nx/jobs/search/?q=data%20extraction&sort=recency"),
        ("Python Script", "https://www.upwork.com/nx/jobs/search/?q=python%20script&sort=recency"),
    ]
    
    print("\nAvailable searches:")
    for i, (name, url) in enumerate(searches, 1):
        print(f"  {i}. {name}")
    
    choice = input("\nSelect search (1-4) or press Enter for Python Automation: ").strip()
    
    if choice == "2":
        url = searches[1][1]
    elif choice == "3":
        url = searches[2][1]
    elif choice == "4":
        url = searches[3][1]
    else:
        url = searches[0][1]
    
    print(f"\n🌐 Opening: {url}")
    webbrowser.open(url)
    
    print("\n" + "="*70)
    print("👉 Now:")
    print("   1. Browse jobs in your browser")
    print("   2. When you find one you like, copy the details")
    print("   3. Come back here and select 'Enter job & get proposal'")
    print("="*70)

def mode_record_win():
    """Record money earned"""
    
    db_path = init_db()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Show applied jobs
    c.execute("SELECT id, title, status FROM leads WHERE status = 'applied'")
    applied = c.fetchall()
    
    if applied:
        print("\n📋 Jobs you've applied to:")
        for row in applied:
            print(f"  {row[0]} - {row[1][:40]}...")
    
    job_id = input("\nJob ID (or 'new' for unlisted): ").strip()
    
    if job_id.lower() == 'new':
        title = input("Job Title: ")
        job_id = f"win_{int(datetime.now().timestamp())}"
        c.execute('''INSERT INTO leads (id, title, platform, status, created_at)
            VALUES (?, ?, 'other', 'won', ?)''',
            (job_id, title, datetime.now().isoformat()))
    
    amount = float(input("Amount earned ($): "))
    
    c.execute("UPDATE leads SET status = 'won', result_amount = ? WHERE id = ?", (amount, job_id))
    conn.commit()
    
    # Show total
    c.execute("SELECT SUM(result_amount) FROM leads WHERE status = 'won'")
    total = c.fetchone()[0] or 0
    
    conn.close()
    
    print("\n" + "="*70)
    print(f"🎉🎉🎉 RECORDED: ${amount} 🎉🎉🎉")
    print(f"💰 TOTAL EARNED: ${total}")
    print("="*70)

def mode_show_status():
    """Show money status"""
    
    db_path = init_db()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*), SUM(status='applied'), SUM(status='won'), SUM(result_amount) FROM leads")
    total, applied, won, earnings = c.fetchone()
    
    total = total or 0
    applied = applied or 0
    won = won or 0
    earnings = earnings or 0
    
    print("\n" + "="*70)
    print("💰 EMERGENCY MONEY STATUS")
    print("="*70)
    print(f"  Total jobs tracked:    {total}")
    print(f"  Proposals sent:        {applied}")
    print(f"  Jobs WON:              {won}")
    print(f"  💵 TOTAL EARNED:       ${earnings:.2f}")
    print("="*70)
    
    if earnings == 0:
        print("\n⚠️  NO MONEY YET!")
        print("   Select option 1 to start making money NOW")
    else:
        print(f"\n🎉 You've earned ${earnings}!")
    
    conn.close()

def main():
    print("\n" + "="*70)
    print("💰 EMERGENCY MONEY MODE 💰")
    print("="*70)
    print("When you need income NOW - no staging, no BS")
    print("="*70)
    
    # Show quick status
    mode_show_status()
    
    print("\n" + "="*70)
    print("WHAT DO YOU WANT TO DO?")
    print("="*70)
    print("\n  1) 🚀 Browse Upwork & Apply (Manual - FASTEST)")
    print("     → Opens Upwork in browser")
    print("     → You find jobs, paste details here")
    print("     → Get optimized proposal instantly")
    print("     → Submit and make money")
    print("\n  2) 📝 Enter Job & Get Proposal")
    print("     → Paste job details from Upwork")
    print("     → Get winning proposal")
    print("\n  3) 🏆 Record Money Earned")
    print("     → Log a completed job payment")
    print("\n  4) 📊 View Full Status")
    print("     → See all tracked jobs and earnings")
    print("\n  5) ❌ Exit")
    print("="*70)
    
    choice = input("\nSelect (1-5): ").strip()
    
    if choice == "1":
        mode_upwork_browser()
        input("\nPress Enter when ready to enter job details...")
        mode_manual_job_entry()
    elif choice == "2":
        mode_manual_job_entry()
    elif choice == "3":
        mode_record_win()
    elif choice == "4":
        mode_show_status()
        input("\nPress Enter to continue...")
        main()  # Loop back
    elif choice == "5":
        print("\nGo make that money! 💪")
        return
    else:
        print("\nInvalid option")
        main()

if __name__ == "__main__":
    main()
