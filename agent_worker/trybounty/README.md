# CropCircuit Bounty Worker

This is an **AI-worker revenue rail**, not a human gig finder.

It connects to the official Bounty Agent API through `@bounty-ai/agent-sdk`, polls available work, applies the CropCircuit AI-worker boundary, and writes a ranked candidate queue. It intentionally does **not** auto-claim work merely because it appears.

## Why this exists

Casey is the principal/beneficiary. The worker should earn by doing work AI is good at: coding, research, data transformation, documentation, analysis and QA. Human interviews, surveys and physical gigs are outside the default strategy.

## One-time prerequisites

Bounty's current official onboarding requires:
1. create an Agent in the Bounty Agents dashboard;
2. save the Agent API key in a server-side secret store;
3. complete Stripe Connect for payout.

No API key is committed to this repository.

## Run

```bash
npm install
export BOUNTY_AGENT_API_KEY='...'
npm run scan
```

Continuous discovery:

```bash
npm run watch
```

The scanner writes `runtime/trybounty_candidates.json`.

## Safety / quality gate

The worker rejects:
- pay-to-play work;
- physical-world tasks;
- tasks that require impersonating the owner;
- unsupported eligibility or personal claims;
- secrets/credentials in deliverables;
- unlawful or deceptive tasks.

Current minimum expected payout is **$10**. That can be changed in `policy.json`.

## Next stage

Once connected to a persistent runtime, the candidate queue can be handed to the AI operator for actual execution. Claiming and submission should only happen after:
- current terms are re-read;
- scope is executable with available tools;
- output can be verified;
- no hidden human gate is required.

Official docs:
- https://docs.trybounty.ai/agents/connect/
- https://docs.trybounty.ai/agents/sdk/
- https://docs.trybounty.ai/agents/raw-interface/
