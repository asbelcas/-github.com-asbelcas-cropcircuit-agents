#!/usr/bin/env python3
"""
Kimi Companion - Task delegation and review system for kimi-cli
Inspired by OpenAI's codex-plugin-cc architecture
"""

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# State directory for job tracking
STATE_DIR = Path.home() / ".kimi" / "kimi-plugin-state"
JOBS_DIR = STATE_DIR / "jobs"


def ensure_state_dirs():
    """Create state directories if they don't exist."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"


def create_job(job_type: str, prompt: str, background: bool = False) -> dict:
    """Create a new job record."""
    ensure_state_dirs()
    job_id = generate_job_id()
    job = {
        "id": job_id,
        "type": job_type,
        "prompt": prompt,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "background": background,
        "result": None,
        "pid": None
    }
    
    job_file = JOBS_DIR / f"{job_id}.json"
    with open(job_file, 'w') as f:
        json.dump(job, f, indent=2)
    
    return job


def update_job(job_id: str, updates: dict):
    """Update a job record."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if not job_file.exists():
        return None
    
    with open(job_file, 'r') as f:
        job = json.load(f)
    
    job.update(updates)
    
    with open(job_file, 'w') as f:
        json.dump(job, f, indent=2)
    
    return job


def get_job(job_id: str) -> Optional[dict]:
    """Get a job by ID."""
    job_file = JOBS_DIR / f"{job_id}.json"
    if not job_file.exists():
        return None
    
    with open(job_file, 'r') as f:
        return json.load(f)


def list_jobs(all_jobs: bool = False) -> list:
    """List jobs, optionally including completed ones."""
    ensure_state_dirs()
    jobs = []
    
    for job_file in sorted(JOBS_DIR.glob("*.json"), reverse=True):
        with open(job_file, 'r') as f:
            job = json.load(f)
        
        if all_jobs or job.get("status") != "completed":
            jobs.append(job)
    
    return jobs[:20]  # Limit to last 20


def run_kimi_task(prompt: str, job_id: str) -> str:
    """Run a kimi task and capture output."""
    # Update job to running
    update_job(job_id, {"status": "running", "started_at": datetime.now().isoformat()})
    
    # Run kimi with the prompt
    try:
        result = subprocess.run(
            ["kimi", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]: {result.stderr}"
        
        # Update job with result
        update_job(job_id, {
            "status": "completed",
            "result": output,
            "completed_at": datetime.now().isoformat(),
            "exit_code": result.returncode
        })
        
        return output
        
    except subprocess.TimeoutExpired:
        update_job(job_id, {
            "status": "timeout",
            "result": "Task timed out after 5 minutes",
            "completed_at": datetime.now().isoformat()
        })
        return "Task timed out"
    except Exception as e:
        update_job(job_id, {
            "status": "error",
            "result": str(e),
            "completed_at": datetime.now().isoformat()
        })
        return f"Error: {e}"


def cmd_task(args):
    """Execute a kimi task."""
    prompt = " ".join(args.prompt) if isinstance(args.prompt, list) else args.prompt
    
    if not prompt:
        print("Error: No prompt provided")
        return 1
    
    job = create_job("task", prompt, background=args.background)
    
    if args.background:
        # Start in background
        import multiprocessing
        process = multiprocessing.Process(target=run_kimi_task, args=(prompt, job["id"]))
        process.start()
        
        update_job(job["id"], {"pid": process.pid})
        print(f"Task started in background.")
        print(f"Job ID: {job['id']}")
        print(f"Check status: kimi-task status {job['id']}")
        return 0
    else:
        # Run foreground
        print(f"Running task... (Job ID: {job['id']})")
        result = run_kimi_task(prompt, job["id"])
        print("\n" + "="*60)
        print(result)
        return 0


def cmd_status(args):
    """Check job status."""
    if args.job_id:
        job = get_job(args.job_id)
        if not job:
            print(f"Job {args.job_id} not found")
            return 1
        
        print(f"Job: {job['id']}")
        print(f"Type: {job['type']}")
        print(f"Status: {job['status']}")
        print(f"Created: {job['created_at']}")
        if job.get('started_at'):
            print(f"Started: {job['started_at']}")
        if job.get('completed_at'):
            print(f"Completed: {job['completed_at']}")
    else:
        jobs = list_jobs(all_jobs=args.all)
        if not jobs:
            print("No jobs found")
            return 0
        
        print(f"{'Job ID':<25} {'Type':<12} {'Status':<12} {'Created'}")
        print("-" * 70)
        for job in jobs:
            short_id = job['id'][:20] + "..." if len(job['id']) > 23 else job['id']
            print(f"{short_id:<25} {job['type']:<12} {job['status']:<12} {job['created_at'][:19]}")
    
    return 0


def cmd_result(args):
    """Get job result."""
    if not args.job_id:
        print("Error: Job ID required")
        return 1
    
    job = get_job(args.job_id)
    if not job:
        print(f"Job {args.job_id} not found")
        return 1
    
    if job['status'] not in ['completed', 'error', 'timeout']:
        print(f"Job status: {job['status']}")
        print("Result not yet available")
        return 0
    
    if args.json:
        print(json.dumps(job, indent=2))
    else:
        print(f"Result for job {job['id']}:")
        print("="*60)
        print(job.get('result', 'No result'))
    
    return 0


def cmd_cancel(args):
    """Cancel a running job."""
    if not args.job_id:
        print("Error: Job ID required")
        return 1
    
    job = get_job(args.job_id)
    if not job:
        print(f"Job {args.job_id} not found")
        return 1
    
    if job['status'] != 'running':
        print(f"Job is not running (status: {job['status']})")
        return 0
    
    # Try to kill the process
    if job.get('pid'):
        try:
            os.kill(job['pid'], 9)
            print(f"Process {job['pid']} killed")
        except ProcessLookupError:
            print(f"Process {job['pid']} not found")
    
    update_job(args.job_id, {
        "status": "cancelled",
        "completed_at": datetime.now().isoformat()
    })
    
    print(f"Job {args.job_id} cancelled")
    return 0


def cmd_review(args):
    """Review code using kimi."""
    # Collect git context
    try:
        diff = subprocess.run(
            ["git", "diff", "--cached", "--stat"],
            capture_output=True,
            text=True
        ).stdout
        
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        ).stdout
    except:
        diff = ""
        status = ""
    
    # Build review prompt
    prompt = """Review the following code changes. Focus on:
1. Bugs and logic errors
2. Security issues
3. Performance problems
4. Code style improvements

Git status:
"""
    if status:
        prompt += status + "\n\n"
    if diff:
        prompt += "Changes:\n" + diff + "\n\n"
    
    prompt += "Please provide a detailed code review."
    
    job = create_job("review", prompt, background=args.background)
    
    if args.background:
        import multiprocessing
        process = multiprocessing.Process(target=run_kimi_task, args=(prompt, job["id"]))
        process.start()
        update_job(job["id"], {"pid": process.pid})
        print(f"Review started in background. Job ID: {job['id']}")
        return 0
    else:
        print("Running code review...")
        result = run_kimi_task(prompt, job["id"])
        print("\n" + "="*60)
        print(result)
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Kimi Companion - Task delegation for kimi-cli"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # task command
    task_parser = subparsers.add_parser("task", help="Run a kimi task")
    task_parser.add_argument("prompt", nargs="+", help="Task prompt")
    task_parser.add_argument("--background", "-b", action="store_true",
                            help="Run in background")
    task_parser.add_argument("--wait", "-w", action="store_true",
                            help="Wait for completion (default)")
    
    # status command
    status_parser = subparsers.add_parser("status", help="Check job status")
    status_parser.add_argument("job_id", nargs="?", help="Job ID to check")
    status_parser.add_argument("--all", "-a", action="store_true",
                              help="Show all jobs including completed")
    
    # result command
    result_parser = subparsers.add_parser("result", help="Get job result")
    result_parser.add_argument("job_id", help="Job ID")
    result_parser.add_argument("--json", "-j", action="store_true",
                              help="Output as JSON")
    
    # cancel command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="Job ID to cancel")
    
    # review command
    review_parser = subparsers.add_parser("review", help="Review code changes")
    review_parser.add_argument("--background", "-b", action="store_true",
                              help="Run in background")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    commands = {
        "task": cmd_task,
        "status": cmd_status,
        "result": cmd_result,
        "cancel": cmd_cancel,
        "review": cmd_review,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
