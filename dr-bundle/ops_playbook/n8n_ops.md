# n8n ops — CropCircuit workflow automation
- Instance: localhost:5678, managed by user systemd `cropcircuit-n8n.service`.
  NEVER run `docker run` manually for the service instance (systemd owns it).
- Env gotchas (all required): --user 1001:1001 (host uid), -e HOME=/home/node
  (else mkdir /.n8n EACCES), cache volume at /home/node/.cache (else EACCES),
  NODE_FUNCTION_ALLOW_BUILTIN=fs,path for Code-node filesystem.
- Workflow lifecycle (CLI-only): build JSON on host → docker cp →
  `docker exec cropcircuit-n8n n8n import:workflow --input=/tmp/x.json` (needs unique
  top-level "id"; purge old row from database.sqlite first to re-import same id) →
  test with a one-shot container: stop service, docker run --rm ... execute --id=X
  (REQUIRES an executeWorkflowTrigger node; the running instance holds port 5679) →
  activate via sqlite UPDATE workflow_entity SET active=1 → start service.
- n8n 2.x PUBLISH MODEL (hard-won): setting active=1 in sqlite does NOT arm triggers —
  workflow_publication_trigger_status stays empty and schedules never fire. CLI
  publish:workflow writes DB but warns "changes will not take effect if n8n is
  running", and the internal REST prefix is not /rest or /api/v1 (public-API only;
  never found the frontend mount). SOLUTION: keep workflows INACTIVE and drive them
  with systemd: cropcircuit-demandscan.service (oneshot: stop n8n → docker run --rm
  execute --id=... → start n8n) + cropcircuit-demandscan.timer (*:17, 2min jitter,
  persistent). Verified working; also immune to the broker-port conflict.
- HTTP Request node: use options.response.responseFormat=text when parsing feeds in
  Code; n8n may otherwise pre-parse. Handle both string and object in Code.
- Multiple fetch branches MUST converge through a Merge node (append) or the next node
  executes once per branch and overwrites state files.
- Secrets: n8n/owner.json (600) has API key + credential ids; HA token lives only as an
  n8n credential; never echo env files (n8n.env is 600 and secret-bearing).
- Feed findings: reddit search.rss = 429-prone (retry + accept zero-hour); PullPush and
  ArcticShift block agents; permies has no RSS; Gardening SE tag feed = reliable Atom.
