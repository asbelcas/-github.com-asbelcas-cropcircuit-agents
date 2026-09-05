# Task Board

| ID | Objective | Owner | Status | Approval | Acceptance evidence |
|---|---|---|---|---|---|
| GOV-20260813-01 | Preserve directive, references, registry, and bounded discovery test | Codex | Complete | None; documentation only | Policy discovery test and diff review |
| OPS-VERIFY-TIMER | Verify Operations Manager timer liveness from a user-bus-capable environment | Operations Manager / Codex | Complete (2026-09-04 overnight audit) | None; read-only | `cropcircuit-operations-manager.timer` confirmed live from user bus; `cycle_completed` every ~15 min, 0 errors in service.log |
| CC-FUNNEL-AUDIT-001 | Audit customer-one funnel using synthetic cases | Codex | Completed; independently verified | None | Read-only report plus focused synthetic tests |
| CC-FUNNEL-REMEDIATE-001 | Correct deadline, intake, fifth/sixth capacity, and test-digest gates | Codex | Completed; independently verified | None; local safety repair | 5 remediation tests, 7 state-machine tests, secret-safety test |
| CC-CUSTOMER-CLEANUP-001 | Prepare coherent customer-facing name/timing/stage/privacy/terms cleanup | Kimi | Awaiting Casey approval | Casey | `CUSTOMER_FACING_CLEANUP_PACKET.md` |
| REL-20260828-01 | Capture release baseline and identify public-release blockers | Kimi/Codex | Complete | None; read-only | `CLOUDFLARE_RELEASE_BASELINE_2026-08-28.md` |
| REL-20260828-02 | Approve authoritative offer catalog and apply customer-facing reconciliation | Kimi/Codex | Pending | Casey | Catalog sign-off, deployed-route and checkout verification |
| REL-20260828-03 | Redirect/TLS/origin/email/webhook/restore release gates | Kimi/Codex | Pending | Casey for external/configuration changes | Gate evidence and rollback proof |

Use `../manager/tasks.jsonl` for executable manager work. Add no vague tasks.
