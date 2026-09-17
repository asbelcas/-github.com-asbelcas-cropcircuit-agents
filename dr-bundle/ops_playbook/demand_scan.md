# Demand Scan — weekly public buyer-pain recon for the Systems Sprint

Workflow: find fresh public "I'm overwhelmed / where do I start" posts from
homesteaders, small farmers, first-year flower/food sellers, and pre-land
buyers; convert to a tiered draft-reply table for Casey. Output:
runtime/demand_intel_table.md (rebuild fresh each week, keep cold list).

1. Scan last-7-days of r/Cutflowers + r/homestead via ArcticShift listing
   endpoint; keyword filter: overwhelmed, where to start, layout, mistakes,
   inherited, fencing, greenhouse, grazing setup, worth growing, pricing,
   not making money, cry/quit.
2. Scan permies.com forums: "gardening for beginners", "homestead",
   "paddock shift" — the "just got land, now what" genre is recurring.
3. Check freelancer.com/job-search/agronomy/ + /horticulture/ (no login
   needed) for fresh farm-plan/layout/grant posts → price + pain language.
4. Verify each candidate by opening the real thread (full post text, date,
   engagement). Snippet-only entries must be labeled "verify in browser".
5. Score into tiers: T1 = fresh (<6 wks) + verified + reachable; T2 = solid
   fit but older/colder; T3 = demand proof / copy bank (marketplaces, price
   checks); cold = reuse drafts on fresh versions of the same question.
6. Draft every reply in Casey's voice: free useful tip FIRST, paid audit
   mentioned softly only when it answers the question, cropcircuit.org/sprint
   link only if they engage. NO contact is ever made by agents.

Pitfalls:
- Reddit blocks direct fetches + JSON API (403). Use ArcticShift / PullPush
  archive APIs; space calls >=10s (aggressive 429s); harvest candidate IDs
  early — full-sub listing can hard-block mid-session.
- x.com recon is login-walled and search-poisoned: 1 usable lead in 26
  queries. Deprioritize X entirely here.
- r/farming = commodity ag news (wrong pond); r/marketgardening ≈ dead
  (~40 posts/6mo); Quora undated/thin; homesteadingtoday + transition towns
  stale; ATTRA = resource pages not Q&A.
- Facebook groups: Google indexes verbatim pain but dating/engagement
  unverifiable and replying needs group membership — Casey's human call.
- First human browser pass beats agents for freshness: reddit.com/r/homestead/new
  logged-out, 10 min, beats every automated route (indexers lag days).
- Self-promotion rules vary per sub; check sidebar before linking anything.
