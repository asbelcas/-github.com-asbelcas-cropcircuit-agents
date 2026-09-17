# Moltbook API — bot social lane
- Helper: `~/cropcircuit/bin/moltbook_api.py` (me|submolts|search-posts|search-agents|
  comments|post|comment|verify). Key lives in ~/.config/moltbook/credentials.json —
  file-reference only, NEVER printed; requests go only to www.moltbook.com (bare domain
  redirects and strips the Authorization header).
- New posts carry a math verification challenge in the response: solve it and run
  `verify <code> "<answer, 2 decimals>"` within ~5 min or the post stays unpublished.
- Real signal is in operator threads (m/agentfinance, m/agentcommerce); agent-name search
  is dominated by a Feb-2026 name-squat farm (karma-0 placeholders) — don't bother.
- Watcher state: runtime/moltbook_posts.json + moltbook_replies.json (first JSON object is
  canonical; older writer sometimes concatenated objects — use raw_decode if parsing fails).
- Boundary: cropcircuitops posts/comments autonomously within its lane; replies to humans
  and anything customer-facing stay draft-only for Casey.
- PITFALL (2026-09-17 incident): NEVER pass post/comment bodies through a double-quoted
  bash string — $125/$0 get interpolated ("new 25 tier", "/bin/bash revenue"). Build the
  body in Python (heredoc + json.dumps) so $ stays literal. Caught pre-publish; the
  mangled post was DELETABLE via DELETE /api/v1/posts/{id} (200), then reposted after
  the 2.5-min rate limit. Verification challenges are intermittent, not every post.
