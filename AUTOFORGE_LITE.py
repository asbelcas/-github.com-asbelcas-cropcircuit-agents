#!/usr/bin/env python3
"""
AUTOFORGE-LITE v1.0
Calibrated Autonomy System for Freelance Automation
Based on: Contract-First Architecture, Failure Ledger, Confidence-Gated Autonomy

AUTONOMY LEVELS:
- Level 4: Full autonomy (monitoring, drafting, tracking)
- Level 3: Human checkpoint (approvals required before action)
- Level 2: Human required (complex decisions)
- Level 1: Full manual (system paused)
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable
from enum import Enum
import threading

# Configuration
CONFIG = {
    "mode": "AUTOFORGE",
    "autonomy_level": 4,  # Starts at 4, degrades to 3 on uncertainty
    "checkpoint_required": True,
    "token_budget_daily": 100000,  # Time budget proxy
    "pause_on_uncertainty": True,
}

class AutonomyLevel(Enum):
    FULL_MANUAL = 1      # System paused
    HUMAN_REQUIRED = 2   # All decisions need human
    CHECKPOINT = 3       # Pauses for approval on critical actions
    FULL_AUTO = 4        # Autonomous on safe tasks

@dataclass
class Contract:
    """Formal specification for a task"""
    task_id: str
    task_type: str  # "opportunity_scan", "proposal_draft", "response_compose"
    input_spec: Dict
    output_spec: Dict
    success_criteria: List[str]
    budget_tokens: int
    autonomy_level_required: int  # Min level to execute without checkpoint
    human_approval_required: bool
    
@dataclass
class FailureLedgerEntry:
    """Log of failed attempts for learning"""
    timestamp: str
    task_id: str
    attempt_number: int
    approach: str
    failure_reason: str
    postmortem_tag: str  # Semantic summary
    suggested_alternative: str

@dataclass
class Checkpoint:
    """Human approval checkpoint"""
    checkpoint_id: str
    task_id: str
    autonomy_level: int
    reason: str
    data_presented: Dict
    options: List[str]
    human_decision: Optional[str] = None
    timestamp_created: str = None
    timestamp_resolved: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp_created is None:
            self.timestamp_created = datetime.now().isoformat()

class FailureLedger:
    """Persistent memory of failures for in-context learning"""
    
    def __init__(self, db_path="/home/asbelcas/rm-qpt/autoforge_ledger.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                task_id TEXT,
                attempt_number INTEGER,
                approach TEXT,
                failure_reason TEXT,
                postmortem_tag TEXT,
                suggested_alternative TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def log_failure(self, entry: FailureLedgerEntry):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO failures 
            (timestamp, task_id, attempt_number, approach, failure_reason, postmortem_tag, suggested_alternative)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.timestamp, entry.task_id, entry.attempt_number,
            entry.approach, entry.failure_reason, entry.postmortem_tag,
            entry.suggested_alternative
        ))
        conn.commit()
        conn.close()
    
    def get_relevant_failures(self, task_type: str, limit: int = 5) -> List[FailureLedgerEntry]:
        """Get semantically relevant failure history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM failures 
            WHERE task_id LIKE ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (f"%{task_type}%", limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        entries = []
        for row in rows:
            entries.append(FailureLedgerEntry(
                timestamp=row[1],
                task_id=row[2],
                attempt_number=row[3],
                approach=row[4],
                failure_reason=row[5],
                postmortem_tag=row[6],
                suggested_alternative=row[7]
            ))
        return entries
    
    def get_failure_summary(self, task_id: str) -> str:
        """Generate meta-summary of failures for a task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT postmortem_tag, COUNT(*) as count 
            FROM failures 
            WHERE task_id = ? 
            GROUP BY postmortem_tag 
            ORDER BY count DESC
        ''', (task_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return "No prior failures for this task type."
        
        summary = "Failure pattern analysis:\n"
        for tag, count in results:
            summary += f"  - {tag}: {count} occurrences\n"
        return summary

class CheckpointManager:
    """Manages human approval checkpoints"""
    
    def __init__(self, checkpoint_dir="/home/asbelcas/rm-qpt/checkpoints"):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)
        self.pending_checkpoints: Dict[str, Checkpoint] = {}
        self._load_pending()
    
    def _load_pending(self):
        """Load pending checkpoints from disk"""
        for filename in os.listdir(self.checkpoint_dir):
            if filename.endswith("_pending.json"):
                with open(os.path.join(self.checkpoint_dir, filename), 'r') as f:
                    data = json.load(f)
                    cp = Checkpoint(**data)
                    self.pending_checkpoints[cp.checkpoint_id] = cp
    
    def create_checkpoint(self, task_id: str, reason: str, data: Dict, options: List[str]) -> str:
        """Create a checkpoint and pause for human approval"""
        checkpoint_id = f"cp_{task_id}_{int(time.time())}"
        
        cp = Checkpoint(
            checkpoint_id=checkpoint_id,
            task_id=task_id,
            autonomy_level=3,
            reason=reason,
            data_presented=data,
            options=options
        )
        
        # Save to disk
        filepath = os.path.join(self.checkpoint_dir, f"{checkpoint_id}_pending.json")
        with open(filepath, 'w') as f:
            json.dump(asdict(cp), f, indent=2)
        
        self.pending_checkpoints[checkpoint_id] = cp
        
        # Create human-readable notification
        notification = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    ⏸️  CHECKPOINT REQUIRED                        ║
╚══════════════════════════════════════════════════════════════════╝

Task: {task_id}
Reason: {reason}
Checkpoint ID: {checkpoint_id}

Data Presented:
{json.dumps(data, indent=2)}

Options:
"""
        for i, option in enumerate(options, 1):
            notification += f"  {i}. {option}\n"
        
        notification += f"""
To approve:
  echo "{checkpoint_id}:approve" >> /home/asbelcas/rm-qpt/checkpoint_responses.txt

To reject:
  echo "{checkpoint_id}:reject" >> /home/asbelcas/rm-qpt/checkpoint_responses.txt

File: {filepath}
"""
        
        # Save notification
        with open(os.path.join(self.checkpoint_dir, f"{checkpoint_id}_notification.txt"), 'w') as f:
            f.write(notification)
        
        print(notification)
        
        return checkpoint_id
    
    def check_responses(self) -> List[tuple]:
        """Check for human responses to checkpoints"""
        responses_file = "/home/asbelcas/rm-qpt/checkpoint_responses.txt"
        resolved = []
        
        if not os.path.exists(responses_file):
            return resolved
        
        with open(responses_file, 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                cp_id, decision = line.split(':', 1)
                if cp_id in self.pending_checkpoints:
                    cp = self.pending_checkpoints[cp_id]
                    cp.human_decision = decision
                    cp.timestamp_resolved = datetime.now().isoformat()
                    
                    # Move from pending to resolved
                    pending_path = os.path.join(self.checkpoint_dir, f"{cp_id}_pending.json")
                    resolved_path = os.path.join(self.checkpoint_dir, f"{cp_id}_resolved.json")
                    
                    with open(resolved_path, 'w') as f:
                        json.dump(asdict(cp), f, indent=2)
                    
                    if os.path.exists(pending_path):
                        os.remove(pending_path)
                    
                    del self.pending_checkpoints[cp_id]
                    resolved.append((cp_id, decision))
        
        # Clear responses file
        open(responses_file, 'w').close()
        
        return resolved
    
    def has_pending_checkpoints(self) -> bool:
        """Check if any checkpoints are waiting for human response"""
        # Reload to catch any new ones
        self._load_pending()
        return len(self.pending_checkpoints) > 0

class RoleScout:
    """Role: Opportunity-Scout - Finds job opportunities"""
    
    def __init__(self, ledger: FailureLedger, checkpoint_mgr: CheckpointManager):
        self.ledger = ledger
        self.checkpoint_mgr = checkpoint_mgr
        self.role_name = "Opportunity-Scout"
    
    def scan_opportunities(self) -> List[Dict]:
        """
        Level 4: Autonomous opportunity scanning
        Returns: List of opportunities meeting criteria
        """
        # In real implementation, would scrape Upwork/Fiverr API
        # For now, simulates finding opportunities
        
        opportunities = []
        
        # Check failure ledger for patterns
        failures = self.ledger.get_relevant_failures("opportunity_scan")
        
        # Contract specification for opportunities
        contract = Contract(
            task_id=f"scan_{int(time.time())}",
            task_type="opportunity_scan",
            input_spec={"platforms": ["Upwork", "Fiverr"], "keywords": ["python", "automation"]},
            output_spec={"opportunities": "list of dicts with budget, description, match_score"},
            success_criteria=["At least 5 opportunities found", "Budget >= $100", "Match score >= 0.7"],
            budget_tokens=5000,
            autonomy_level_required=4,
            human_approval_required=False
        )
        
        # Simulate finding opportunities (replace with actual scraping)
        opportunities.append({
            "id": "job_001",
            "platform": "Upwork",
            "title": "Python Automation Script Needed",
            "budget": "$200-500",
            "description": "Need to automate data extraction from website",
            "match_score": 0.95,
            "urgency": "high",
            "proposal_deadline": "24 hours"
        })
        
        opportunities.append({
            "id": "job_002", 
            "platform": "Fiverr",
            "title": "Web Scraping Expert Required",
            "budget": "$150",
            "description": "Scrape product data from e-commerce site",
            "match_score": 0.88,
            "urgency": "medium",
            "proposal_deadline": "3 days"
        })
        
        return opportunities

class RoleDrafter:
    """Role: Proposal-Writer - Drafts job applications"""
    
    def __init__(self, ledger: FailureLedger, checkpoint_mgr: CheckpointManager):
        self.ledger = ledger
        self.checkpoint_mgr = checkpoint_mgr
        self.role_name = "Proposal-Writer"
    
    def draft_proposal(self, opportunity: Dict) -> str:
        """
        Level 4: Draft proposal
        Returns: Draft proposal text
        """
        # Load failure patterns
        failure_summary = self.ledger.get_failure_summary(f"proposal_{opportunity['id']}")
        
        # Draft based on opportunity and failure patterns
        proposal = f"""Hi there,

I can help with your {opportunity['title'].lower()}.

Relevant experience:
• Built automated trading system (2,291 lines Python)
• Expert in web scraping and data extraction  
• Deliver projects in 24-48 hours

My approach:
1. Understand your exact requirements
2. Design robust solution with error handling
3. Build and test thoroughly
4. Deliver with documentation

I can start immediately and have this done within your timeline.

Questions:
1. What specific data do you need extracted?
2. What format do you prefer for delivery (CSV, JSON, etc.)?
3. Are there any anti-bot measures on the target site?

Looking forward to working with you.

Best regards"""
        
        return proposal
    
    def submit_proposal(self, opportunity: Dict, proposal: str) -> bool:
        """
        Level 3: Requires human checkpoint before submitting
        """
        # Create checkpoint
        checkpoint_id = self.checkpoint_mgr.create_checkpoint(
            task_id=f"submit_{opportunity['id']}",
            reason="Proposal ready for submission - requires human approval",
            data={
                "opportunity": opportunity,
                "proposal_text": proposal,
                "platform": opportunity['platform'],
                "estimated_value": opportunity['budget']
            },
            options=[
                "approve - Submit proposal as drafted",
                "edit - I'll modify the proposal first", 
                "reject - Skip this opportunity",
                "pause - Wait for me to review later"
            ]
        )
        
        # System now PAUSES here until human responds
        return False  # Submission pending approval

class RoleResponder:
    """Role: Response-Handler - Manages client communications"""
    
    def __init__(self, ledger: FailureLedger, checkpoint_mgr: CheckpointManager):
        self.ledger = ledger
        self.checkpoint_mgr = checkpoint_mgr
        self.role_name = "Response-Handler"
    
    def draft_response(self, client_message: str, context: Dict) -> str:
        """
        Level 3: Draft response, requires approval before sending
        """
        # Draft response based on message type
        if "budget" in client_message.lower():
            response = "I'm flexible on budget depending on scope. Could you share more details about the specific requirements?"
        elif "timeline" in client_message.lower():
            response = "I can deliver within your timeline. For projects like this, I typically need 24-48 hours. Would that work for you?"
        else:
            response = "Thanks for your message. I'd be happy to help with this project. When would be a good time for a quick call to discuss details?"
        
        # Create checkpoint
        checkpoint_id = self.checkpoint_mgr.create_checkpoint(
            task_id=f"respond_{int(time.time())}",
            reason="Client response requires approval before sending",
            data={
                "client_message": client_message,
                "drafted_response": response,
                "context": context
            },
            options=[
                "send - Send response as drafted",
                "edit - Let me modify the response",
                "custom - I'll write a different response",
                "ignore - Don't respond to this message"
            ]
        )
        
        return checkpoint_id

class AutoforgeLite:
    """Main AUTOFORGE-LITE System"""
    
    def __init__(self):
        self.ledger = FailureLedger()
        self.checkpoint_mgr = CheckpointManager()
        self.scout = RoleScout(self.ledger, self.checkpoint_mgr)
        self.drafter = RoleDrafter(self.ledger, self.checkpoint_mgr)
        self.responder = RoleResponder(self.ledger, self.checkpoint_mgr)
        
        self.autonomy_level = AutonomyLevel.FULL_AUTO
        self.token_budget = CONFIG['token_budget_daily']
        self.running = True
        
        self.log_file = f"/home/asbelcas/rm-qpt/logs/autoforge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        os.makedirs("/home/asbelcas/rm-qpt/logs", exist_ok=True)
        
        self._log("="*70)
        self._log("🔥 AUTOFORGE-LITE v1.0 ACTIVATED")
        self._log("="*70)
        self._log("Autonomy: Level 4 (Calibrated)")
        self._log("Mode: Continuous with Checkpoints")
        self._log("Architecture: Contract-First + Failure Ledger + Confidence-Gated")
        self._log("="*70)
    
    def _log(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        with open(self.log_file, 'a') as f:
            f.write(line + "\n")
    
    def check_autonomy_degradation(self) -> AutonomyLevel:
        """
        Check if system should degrade autonomy level
        Triggers: Budget low, failures accumulating, uncertainty high
        """
        # Check token budget
        if self.token_budget < 20000:  # 20% remaining
            self._log("⚠️ Token budget low - Degrading to Level 3")
            return AutonomyLevel.CHECKPOINT
        
        # Check pending checkpoints
        if self.checkpoint_mgr.has_pending_checkpoints():
            return AutonomyLevel.CHECKPOINT
        
        # Check failure rate (simplified)
        # In real implementation, would analyze ledger patterns
        
        return AutonomyLevel.FULL_AUTO
    
    def process_cycle(self):
        """One full cycle of the AUTOFORGE system"""
        self._log("\n" + "="*70)
        self._log("🔄 PROCESS CYCLE STARTING")
        self._log("="*70)
        
        # Step 1: Scout - Find opportunities (Level 4)
        self._log("\n📡 ROLE: Opportunity-Scout")
        self._log("Task: Scan for new opportunities")
        self._log("Autonomy: Level 4 (Full Auto)")
        
        opportunities = self.scout.scan_opportunities()
        self._log(f"Found {len(opportunities)} opportunities")
        
        # Step 2: Drafter - Draft proposals (Level 4)
        drafted_proposals = []
        for opp in opportunities:
            self._log(f"\n📝 ROLE: Proposal-Writer")
            self._log(f"Task: Draft proposal for {opp['id']}")
            self._log(f"Autonomy: Level 4 (Full Auto)")
            
            proposal = self.drafter.draft_proposal(opp)
            drafted_proposals.append((opp, proposal))
            
            self._log("✅ Proposal drafted")
            
            # Step 3: Check if submission needs approval (Level 3)
            self._log(f"\n⏸️  CHECKPOINT: Submit proposal?")
            self._log(f"Task: Submit proposal for {opp['id']}")
            self._log(f"Autonomy: Level 3 (Human Checkpoint)")
            
            self.drafter.submit_proposal(opp, proposal)
            self._log("⏸️  PAUSED - Waiting for human approval")
        
        # Step 4: Check for human responses
        self._log("\n📥 Checking for human responses...")
        responses = self.checkpoint_mgr.check_responses()
        
        if responses:
            for cp_id, decision in responses:
                self._log(f"✅ Checkpoint {cp_id}: {decision}")
                # Process decision
                if decision == "approve":
                    self._log("🚀 Executing approved action...")
                elif decision == "reject":
                    self._log("❌ Skipping rejected action...")
        else:
            self._log("⏳ No responses yet")
        
        # Step 5: Check autonomy degradation
        new_level = self.check_autonomy_degradation()
        if new_level != self.autonomy_level:
            self.autonomy_level = new_level
            self._log(f"\n🔄 Autonomy level changed: {new_level.name}")
        
        # Step 6: Save state
        self._save_state()
        
        self._log("\n" + "="*70)
        self._log("✅ PROCESS CYCLE COMPLETE")
        self._log("="*70)
    
    def _save_state(self):
        """Save system state"""
        state = {
            "timestamp": datetime.now().isoformat(),
            "autonomy_level": self.autonomy_level.name,
            "token_budget": self.token_budget,
            "pending_checkpoints": len(self.checkpoint_mgr.pending_checkpoints)
        }
        
        with open("/home/asbelcas/rm-qpt/autoforge_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    def run(self):
        """Main loop"""
        self._log("\n🚀 Starting continuous operation")
        self._log("Press Ctrl+C to stop")
        
        iteration = 0
        try:
            while self.running:
                iteration += 1
                self._log(f"\n{'='*70}")
                self._log(f"ITERATION {iteration}")
                self._log(f"{'='*70}")
                
                self.process_cycle()
                
                # If checkpoints pending, wait for human
                if self.checkpoint_mgr.has_pending_checkpoints():
                    self._log("\n⏸️  CHECKPOINTS PENDING")
                    self._log("System will check for responses every 30 seconds...")
                    
                    while self.checkpoint_mgr.has_pending_checkpoints():
                        time.sleep(30)
                        responses = self.checkpoint_mgr.check_responses()
                        if responses:
                            for cp_id, decision in responses:
                                self._log(f"✅ Response received: {cp_id} = {decision}")
                        else:
                            self._log("⏳ Still waiting for human responses...")
                
                # Sleep between cycles
                self._log("\n😴 Sleeping 5 minutes until next cycle...")
                time.sleep(300)
                
        except KeyboardInterrupt:
            self._log("\n🛑 Stopped by user")
        finally:
            self._save_state()
            self._log("\n✅ AUTOFORGE-LITE shutdown complete")

def main():
    print("="*70)
    print("🔥 AUTOFORGE-LITE v1.0")
    print("Calibrated Autonomy System")
    print("="*70)
    print()
    print("AUTONOMY LEVELS:")
    print("  Level 4: Full Auto (monitoring, drafting)")
    print("  Level 3: Checkpoint (pauses for approval)")
    print("  Level 2: Human Required (complex decisions)")
    print("  Level 1: Full Manual (system paused)")
    print()
    print("CURRENT MODE: Level 4 with auto-degradation")
    print("Checkpoints: ENABLED")
    print("Human approval required for: submissions, responses, spending")
    print()
    print("="*70)
    
    system = AutoforgeLite()
    system.run()

if __name__ == "__main__":
    main()
