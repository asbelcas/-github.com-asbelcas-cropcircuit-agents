#!/usr/bin/env python3
"""
REAL TASK AGGREGATOR
Connects to actual paying platforms and finds real opportunities
"""

import json
import webbrowser
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class RealPlatform:
    """Real money-making platform"""
    name: str
    url: str
    task_types: List[str]
    avg_pay: str
    payment_method: str
    payment_time: str
    signup_time: str
    requirements: List[str]
    status: str = "not_started"  # not_started, pending, active, earning


class RealTaskAggregator:
    """
    Aggregates real opportunities from legitimate platforms
    No simulations - just real data about real platforms
    """
    
    def __init__(self):
        self.platforms = [
            RealPlatform(
                name="Amazon MTurk",
                url="https://worker.mturk.com",
                task_types=["Surveys", "Data entry", "Image tagging", "Transcription"],
                avg_pay="$0.01 - $5.00 per task",
                payment_method="Amazon Payments → Bank",
                payment_time="3-30 days",
                signup_time="24-48 hours approval",
                requirements=["Amazon account", "SSN/Tax ID", "18+ years old"]
            ),
            RealPlatform(
                name="Prolific",
                url="https://www.prolific.co",
                task_types=["Academic surveys", "Research studies"],
                avg_pay="$6-12 per hour",
                payment_method="PayPal",
                payment_time="Instant once approved",
                signup_time="Immediate (after verification)",
                requirements=["PayPal account", "Valid ID", "Good standing"]
            ),
            RealPlatform(
                name="Clickworker",
                url="https://www.clickworker.com",
                task_types=["Surveys", "Text creation", "Categorization", "Research"],
                avg_pay="$0.05 - $1.00 per task",
                payment_method="PayPal or Payoneer",
                payment_time="Weekly (Wednesdays)",
                signup_time="Immediate",
                requirements=["PayPal account", "Pass assessments"]
            ),
            RealPlatform(
                name="UserTesting",
                url="https://www.usertesting.com",
                task_types=["Website testing", "App testing", "Feedback"],
                avg_pay="$10 per 20-minute test",
                payment_method="PayPal",
                payment_time="7 days",
                signup_time="1-2 weeks (after sample test)",
                requirements=["Microphone", "Sample test approval", "PayPal"]
            ),
            RealPlatform(
                name="Appen",
                url="https://appen.com",
                task_types=["AI training", "Data collection", "Transcription", "Translation"],
                avg_pay="$3-15 per hour",
                payment_method="PayPal or Payoneer",
                payment_time="Monthly",
                signup_time="1-2 weeks",
                requirements=["Pass qualifications", "Resume/CV", "Language skills"]
            ),
            RealPlatform(
                name="Fiverr",
                url="https://www.fiverr.com",
                task_types=["Any skill you have", "Digital services", "Creative work"],
                avg_pay="$5-500+ per gig",
                payment_method="PayPal or Bank",
                payment_time="14 days (7 days with Top Rated)",
                signup_time="Immediate",
                requirements=["Skill to sell", "Gig creation"]
            ),
            RealPlatform(
                name="r/beermoney (Reddit)",
                url="https://reddit.com/r/beermoney",
                task_types=["Surveys", "Sign-up bonuses", "Microtasks"],
                avg_pay="$0.50 - $20 per task",
                payment_method="Various (PayPal, crypto, gift cards)",
                payment_time="Varies by offer",
                signup_time="Immediate",
                requirements=["Reddit account", "PayPal for most"]
            ),
            RealPlatform(
                name="Coinbase Learn & Earn",
                url="https://www.coinbase.com/learn",
                task_types=["Watch videos", "Answer quizzes"],
                avg_pay="$3-10 per lesson",
                payment_method="Crypto to Coinbase wallet",
                payment_time="Instant",
                signup_time="Immediate (if available)",
                requirements=["Coinbase account", "Verified identity"]
            ),
        ]
        
        self.earnings_log = []
        self.load_earnings()
    
    def load_earnings(self):
        """Load real earnings from file"""
        try:
            with open('real_earnings.json', 'r') as f:
                data = json.load(f)
                self.earnings_log = data.get('earnings', [])
        except:
            self.earnings_log = []
    
    def save_earnings(self):
        """Save real earnings to file"""
        with open('real_earnings.json', 'w') as f:
            json.dump({
                'updated_at': datetime.now().isoformat(),
                'total_earned': sum(e['amount'] for e in self.earnings_log),
                'earnings': self.earnings_log
            }, f, indent=2)
    
    def add_real_earning(self, platform: str, amount: float, task: str):
        """Add a REAL earning (user must verify this happened)"""
        earning = {
            'timestamp': datetime.now().isoformat(),
            'platform': platform,
            'amount': amount,
            'task': task,
            'verified': False  # User must confirm this is real
        }
        self.earnings_log.append(earning)
        self.save_earnings()
        print(f"✅ Logged: ${amount:.2f} from {platform} for '{task}'")
        print("   Mark as verified once you confirm payment received")
    
    def display_platforms(self):
        """Display all real platforms"""
        print("\n" + "="*80)
        print("  💰 REAL PLATFORMS THAT PAY ACTUAL MONEY")
        print("="*80)
        
        for i, platform in enumerate(self.platforms, 1):
            print(f"\n{i}. {platform.name}")
            print(f"   URL: {platform.url}")
            print(f"   Tasks: {', '.join(platform.task_types)}")
            print(f"   Pay: {platform.avg_pay}")
            print(f"   Payment: {platform.payment_method} ({platform.payment_time})")
            print(f"   Signup: {platform.signup_time}")
            print(f"   Requirements: {', '.join(platform.requirements)}")
            print(f"   Status: {platform.status}")
    
    def get_quick_start_guide(self):
        """Get immediate action steps"""
        print("\n" + "="*80)
        print("  🚀 QUICK START - DO THESE RIGHT NOW")
        print("="*80)
        
        steps = [
            ("1. Coinbase Learn & Earn", 
             "Open Coinbase app → Go to 'Learn' → Watch videos → Earn $3-10",
             "5 minutes", "$3-10 instant"),
            
            ("2. Sign up for Prolific",
             "Go to prolific.co → Create account → Start surveys today",
             "10 minutes", "$5-15/day"),
            
            ("3. Sign up for Clickworker",
             "Go to clickworker.com → Register → Take assessments",
             "20 minutes", "$3-10/day"),
            
            ("4. Sign up for Amazon MTurk",
             "Go to worker.mturk.com → Apply → Wait 24-48hrs for approval",
             "15 minutes", "$5-20/day (after approval)"),
            
            ("5. Check r/beermoney",
             "Go to reddit.com/r/beermoney → Find current high-paying offers",
             "10 minutes", "$5-50 (varies)"),
        ]
        
        for name, action, time, expected in steps:
            print(f"\n{name}")
            print(f"   Action: {action}")
            print(f"   Time: {time}")
            print(f"   Expected: {expected}")
    
    def open_platform(self, platform_number: int):
        """Open platform in browser"""
        if 1 <= platform_number <= len(self.platforms):
            platform = self.platforms[platform_number - 1]
            print(f"\nOpening {platform.name}...")
            print(f"URL: {platform.url}")
            try:
                webbrowser.open(platform.url)
            except:
                print(f"Please manually open: {platform.url}")
        else:
            print("Invalid platform number")
    
    def show_earnings_summary(self):
        """Show real earnings summary"""
        print("\n" + "="*80)
        print("  📊 REAL EARNINGS SUMMARY")
        print("="*80)
        
        if not self.earnings_log:
            print("\n   No earnings logged yet.")
            print("   Start working on real platforms and log your earnings!")
            return
        
        total = sum(e['amount'] for e in self.earnings_log)
        verified = sum(e['amount'] for e in self.earnings_log if e.get('verified'))
        pending = total - verified
        
        print(f"\n   Total Logged: ${total:.2f}")
        print(f"   Verified (Paid): ${verified:.2f}")
        print(f"   Pending: ${pending:.2f}")
        print(f"   Number of Earnings: {len(self.earnings_log)}")
        
        print("\n   Recent Earnings:")
        for earning in self.earnings_log[-5:]:
            status = "✅" if earning.get('verified') else "⏳"
            print(f"   {status} ${earning['amount']:.2f} from {earning['platform']} - {earning['task']}")


def main():
    """Main interactive menu"""
    aggregator = RealTaskAggregator()
    
    while True:
        print("\n" + "="*80)
        print("  💰 REAL TASK AGGREGATOR")
        print("="*80)
        print("\n1. View all platforms")
        print("2. Quick start guide")
        print("3. Open platform in browser")
        print("4. Log real earning")
        print("5. View earnings summary")
        print("6. Exit")
        print("\nNOTE: This tool helps you find REAL work, not fake money.")
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            aggregator.display_platforms()
        elif choice == "2":
            aggregator.get_quick_start_guide()
        elif choice == "3":
            aggregator.display_platforms()
            platform_num = input("\nEnter platform number to open: ").strip()
            if platform_num.isdigit():
                aggregator.open_platform(int(platform_num))
        elif choice == "4":
            print("\nLog a REAL earning (be honest!):")
            platform = input("Platform name: ").strip()
            amount = input("Amount earned ($): ").strip()
            task = input("What you did: ").strip()
            if platform and amount and task:
                try:
                    aggregator.add_real_earning(platform, float(amount), task)
                except ValueError:
                    print("Invalid amount")
        elif choice == "5":
            aggregator.show_earnings_summary()
        elif choice == "6":
            print("\nRemember: Real work = Real money. Good luck!")
            break


if __name__ == "__main__":
    main()
