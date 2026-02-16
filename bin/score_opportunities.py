#!/usr/bin/env python3
import json
import re
import sys

POSITIVE = [
    (r"\bgrant\b|\bdonor\b|\bpartnership\b|\binstitution", 6),
    (r"\brevenue\b|\brecurring\b|\bsubscription\b|\bsales?\b", 7),
    (r"\bcapital\b|\bfunding\b|\bcommitment\b", 6),
    (r"\bcost\b|\bsave\b|\breduce\b|\binfrastructure\b", 4),
    (r"\bmonthly\b|\bbaseline income\b|\blow maintenance\b", 6),
    (r"\bdiversif(y|ied|ication)\b|\bmulti[- ]channel\b", 5),
]
NEGATIVE = [
    (r"\bvanity\b", -8),
    (r"\bsocial growth\b|\bfollowers?\b", -7),
    (r"\bexperimental?\b|\bprototype\b", -6),
    (r"\bone[- ]off\b|\bshort[- ]term spike\b", -8),
    (r"\bmanual\b|\bconstant attention\b", -7),
    (r"\bsingle (source|partner|platform|grant)\b", -10),
]


def score(move_text: str):
    text = move_text.lower()
    score = 0
    for pat, val in POSITIVE:
        if re.search(pat, text):
            score += val
    for pat, val in NEGATIVE:
        if re.search(pat, text):
            score += val
    effort = 3 if re.search(r"\bautomate|script|cron|batch\b", text) else 5
    risk = 2 if re.search(r"\bgrant|partner|donor|recurring|cost reduction\b", text) else 5
    impact = max(1, min(10, score // 2 + 5))
    final = score + impact - effort - risk
    return final, impact, effort, risk


moves = [m for m in sys.stdin.read().splitlines() if m.strip()]
ranked = []
for m in moves:
    s, i, e, r = score(m)
    ranked.append({"move": m, "score": s, "impact": i, "effort": e, "risk": r})

ranked.sort(key=lambda x: x["score"], reverse=True)
print(json.dumps(ranked[:3], indent=2))
