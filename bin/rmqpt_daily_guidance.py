#!/usr/bin/env python3
"""
RM-QPT Daily Guidance Generator

Generates daily strategic guidance using Rheomodal Quantum Process Theory.
Run this each morning to get RM-QPT informed direction for grant sprint.

Usage:
    python3 bin/rmqpt_daily_guidance.py
    python3 bin/rmqpt_daily_guidance.py --format json
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rm_qpt import GrantOrchestratorRMQPTAdapter


def main():
    parser = argparse.ArgumentParser(description="Generate RM-QPT daily guidance")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")
    parser.add_argument("--grant-amount", type=float, default=50000,
                       help="Grant amount (default: 50000)")
    parser.add_argument("--partners", type=int, default=4,
                       help="Required partner count (default: 4)")
    args = parser.parse_args()
    
    # Initialize RM-QPT adapter
    adapter = GrantOrchestratorRMQPTAdapter(
        grant_amount=args.grant_amount,
        partner_required=args.partners
    )
    
    if args.format == "json":
        # Output structured analysis
        analysis = adapter.analyze_outreach_state()
        print(json.dumps(analysis, indent=2, default=str))
    else:
        # Output human-readable guidance
        guidance = adapter.generate_daily_guidance()
        print(guidance)
    
    # Always log the trace
    adapter.log_daily_trace()
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
