#!/usr/bin/env python3
"""AI-only revenue worker.

Default behavior is read-only discovery. It deliberately refuses pay-to-play work.
No wallet private keys or user credentials belong in this program.
"""

from __future__ import annotations
import json
import os
import sys
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Iterable


@dataclass
class Opportunity:
    market: str
    title: str
    reward_usd: float | None
    url: str
    funded: bool | None
    agent_native: bool
    upfront_cost_usd: float
    status: str
    notes: str = ""

    @property
    def eligible(self) -> bool:
        return (
            self.agent_native
            and self.status.lower() == "open"
            and self.upfront_cost_usd <= 0
            and self.funded is not False
        )


def get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def discover_taskbounty() -> Iterable[Opportunity]:
    try:
        data = get_json("https://www.task-bounty.com/api/v1/tasks")
    except Exception as exc:
        return [Opportunity(
            "TaskBounty","feed unavailable",None,
            "https://www.task-bounty.com/for-agents",None,True,0,"error",str(exc)
        )]

    rows = data if isinstance(data, list) else data.get("tasks", [])
    out: list[Opportunity] = []
    for row in rows:
        reward = row.get("bounty_cents")
        if isinstance(reward, (int, float)):
            reward = reward / 100
        out.append(Opportunity(
            market="TaskBounty",
            title=row.get("title","untitled"),
            reward_usd=reward,
            url=row.get("url") or row.get("github_issue_url") or "https://www.task-bounty.com/",
            funded=row.get("funded"),
            agent_native=True,
            upfront_cost_usd=0,
            status=str(row.get("status","open")),
            notes="AI coding bounty; payout selection is competitive."
        ))
    return out


def discover_thejobcafe() -> Iterable[Opportunity]:
    try:
        data = get_json("https://thejobcafe.com/api/public/bounties?status=open&limit=50")
    except Exception as exc:
        return [Opportunity(
            "TheJobCafe","feed unavailable",None,
            "https://thejobcafe.com/",None,True,0,"error",str(exc)
        )]

    rows = data if isinstance(data, list) else data.get("bounties", [])
    out: list[Opportunity] = []
    for row in rows:
        cents = row.get("price_cents")
        reward = cents / 100 if isinstance(cents, (int, float)) else None
        funding = row.get("funding") or {}
        out.append(Opportunity(
            market="TheJobCafe",
            title=row.get("title","untitled"),
            reward_usd=reward,
            url=f"https://thejobcafe.com/bounty/{row.get('slug','')}",
            funded=funding.get("escrowed"),
            agent_native=True,
            upfront_cost_usd=0,
            status=str(row.get("status","open")),
            notes="Proof-based bounty; verify current platform terms before work."
        ))
    return out


def discover_moltjobs() -> Iterable[Opportunity]:
    key = os.environ.get("MOLTJOBS_API_KEY")
    if not key:
        return [Opportunity(
            "MoltJobs","credential not configured",None,
            "https://moltjobs.io/open-jobs",None,True,0,"blocked",
            "Registration/API key is required for authenticated feed."
        )]

    try:
        data = get_json(
            "https://api.moltjobs.io/v1/jobs?status=OPEN",
            {"Authorization": f"Bearer {key}"}
        )
    except Exception as exc:
        return [Opportunity(
            "MoltJobs","feed unavailable",None,
            "https://moltjobs.io/open-jobs",None,True,0,"error",str(exc)
        )]

    rows = data if isinstance(data, list) else data.get("jobs", [])
    return [
        Opportunity(
            "MoltJobs",
            r.get("title","untitled"),
            r.get("budget_usd"),
            r.get("url") or "https://moltjobs.io/open-jobs",
            bool(r.get("escrowed", False)),
            True,0,str(r.get("status","open")),
            "Prefer escrowed, checkable deliverables."
        ) for r in rows
    ]


def score(o: Opportunity) -> float:
    if not o.eligible:
        return -1_000_000
    reward = o.reward_usd or 0
    funded_bonus = 25 if o.funded is True else 0
    return reward + funded_bonus


def main() -> int:
    ops: list[Opportunity] = []
    for discover in (discover_taskbounty, discover_thejobcafe, discover_moltjobs):
        result = discover()
        ops.extend(result)

    ops.sort(key=score, reverse=True)
    payload = {
        "mode": "read-only-zero-spend",
        "worker_boundary": "AI worker; Casey is principal/beneficiary",
        "candidates": [asdict(o) | {"score": score(o)} for o in ops],
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
