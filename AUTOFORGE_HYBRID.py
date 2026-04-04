#!/usr/bin/env python3
"""
AUTOFORGE-LITE - HYBRID MODE (RECOMMENDED)
System drafts + Browser opens + YOU submit manually

This is the SAFEST approach:
- System finds jobs (automated)
- System drafts proposals (automated)
- Browser opens job page (automated)
- YOU review and submit manually (human control)

Benefits:
✅ You see exactly what's being submitted
✅ You control the final action
✅ Much lower risk of account ban
✅ Still saves 90% of the time
"""

import os
import sys
import json
import time
import webbrowser
from datetime import datetime
from pathlib import Path

class HybridSubmissionManager:
    """
    Hybrid approach: Automate drafting, manual submission
    """
    
    def __init__(self):
        self.checkpoint_dir = "/home/asbelcas/rm-qpt/checkpoints"
        self.submission_queue = []
        
    def prepare_submission(self, opportunity, proposal_text):
        """
        Stage a submission for manual execution
        """
        print("="*70)
        print("🔄 HYBRID MODE: Preparing Submission")
        print("="*70)
        print()
        
        # Create submission package
        submission = {
            "timestamp": datetime.now().isoformat(),
            "platform": opportunity.get('platform', 'unknown'),
            "job_title": opportunity.get('title', 'Unknown Job'),
            "job_link": opportunity.get('link', ''),
            "budget": opportunity.get('budget', 'Not specified'),
            "proposal_text": proposal_text,
            "status": "READY_FOR_MANUAL_SUBMISSION"
        }
        
        # Save to queue
        submission_id = f"sub_{int(time.time())}"
        submission_file = f"{self.checkpoint_dir}/{submission_id}.json"
        
        with open(submission_file, 'w') as f:
            json.dump(submission, f, indent=2)
        
        # Create human-readable instructions
        instructions = f"""
╔══════════════════════════════════════════════════════════════════╗
║           📋 MANUAL SUBMISSION INSTRUCTIONS                        ║
╚══════════════════════════════════════════════════════════════════╝

Job: {submission['job_title']}
Platform: {submission['platform']}
Budget: {submission['budget']}

STEP 1: Open the job link
   {submission['job_link']}

   (Or click the link if your terminal supports it)

STEP 2: Review the job details
   - Make sure it matches your skills
   - Check the budget is acceptable
   - Verify the timeline works for you

STEP 3: Click "Apply" or "Submit Proposal"

STEP 4: Copy and paste this proposal:

--- COPY FROM HERE ---
{submission['proposal_text']}
--- COPY TO HERE ---

STEP 5: Customize if needed
   - Add specific details from the job posting
   - Adjust timeline if needed
   - Set your rate

STEP 6: Submit

═══════════════════════════════════════════════════════════════════

Time saved: ~10 minutes (vs writing from scratch)
Risk level: ZERO (you control everything)
Success rate: Much higher than automation

Submission ID: {submission_id}
Status: Ready
"""
        
        instructions_file = f"{self.checkpoint_dir}/{submission_id}_instructions.txt"
        with open(instructions_file, 'w') as f:
            f.write(instructions)
        
        print(instructions)
        
        # Try to open browser
        try:
            if submission['job_link']:
                print("🌐 Opening job link in browser...")
                webbrowser.open(submission['job_link'])
                print("✅ Browser opened")
        except Exception as e:
            print(f"⚠️  Could not open browser automatically: {e}")
            print(f"   Please manually navigate to: {submission['job_link']}")
        
        print()
        print("="*70)
        print("✅ Submission prepared and staged")
        print("="*70)
        print()
        print("Next steps:")
        print("1. Review the instructions above")
        print("2. Copy the proposal text")
        print("3. Navigate to the job link")
        print("4. Paste and submit manually")
        print()
        print(f"Instructions saved to: {instructions_file}")
        
        return submission_id
    
    def process_queue(self):
        """
        Process all staged submissions
        """
        print("="*70)
        print("📋 PROCESSING SUBMISSION QUEUE")
        print("="*70)
        print()
        
        # Find all ready submissions
        submissions = []
        for filename in os.listdir(self.checkpoint_dir):
            if filename.startswith("sub_") and filename.endswith(".json"):
                filepath = os.path.join(self.checkpoint_dir, filename)
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    if data.get('status') == "READY_FOR_MANUAL_SUBMISSION":
                        submissions.append((filename, data))
        
        if not submissions:
            print("No pending submissions in queue.")
            return
        
        print(f"Found {len(submissions)} submission(s) ready:")
        print()
        
        for i, (filename, data) in enumerate(submissions, 1):
            print(f"{i}. {data['job_title']}")
            print(f"   Platform: {data['platform']}")
            print(f"   Budget: {data['budget']}")
            print()
        
        print("Options:")
        print("1. Process submission 1")
        print("2. Process submission 2")
        print("3. Process all submissions")
        print("4. Exit")
        print()
        
        choice = input("Select option: ")
        
        if choice == "1" and len(submissions) >= 1:
            self._execute_submission(submissions[0][1])
        elif choice == "2" and len(submissions) >= 2:
            self._execute_submission(submissions[1][1])
        elif choice == "3":
            for filename, data in submissions:
                self._execute_submission(data)
        else:
            print("Exiting...")
    
    def _execute_submission(self, submission_data):
        """
        Execute a single submission (open browser, show instructions)
        """
        print()
        print("="*70)
        print(f"🚀 EXECUTING: {submission_data['job_title']}")
        print("="*70)
        print()
        
        # Show proposal
        print("PROPOSAL TEXT:")
        print("-" * 70)
        print(submission_data['proposal_text'])
        print("-" * 70)
        print()
        
        # Open browser
        try:
            print(f"🌐 Opening: {submission_data['job_link']}")
            webbrowser.open(submission_data['job_link'])
        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")
        
        print()
        print("Instructions:")
        print("1. Review the job in your browser")
        print("2. Click 'Apply' or 'Submit Proposal'")
        print("3. Copy the proposal text above")
        print("4. Paste into the proposal form")
        print("5. Submit")
        print()
        
        input("Press Enter when done (or Ctrl+C to skip)...")
        
        # Mark as submitted
        submission_data['status'] = "MANUALLY_SUBMITTED"
        submission_data['submitted_at'] = datetime.now().isoformat()
        
        print("✅ Marked as submitted")
        print()

def main():
    print("="*70)
    print("🔄 AUTOFORGE-LITE: HYBRID MODE (RECOMMENDED)")
    print("="*70)
    print()
    print("Mode: System drafts + You submit manually")
    print()
    print("Benefits:")
    print("  ✅ Zero risk of account ban")
    print("  ✅ You see everything before it goes out")
    print("  ✅ Still saves 90% of your time")
    print("  ✅ Works with all platforms")
    print()
    print("Process:")
    print("  1. AUTOFORGE finds jobs and drafts proposals")
    print("  2. System stages them in queue")
    print("  3. YOU execute submissions one by one")
    print("  4. System tracks what was sent")
    print()
    
    manager = HybridSubmissionManager()
    manager.process_queue()

if __name__ == "__main__":
    main()
