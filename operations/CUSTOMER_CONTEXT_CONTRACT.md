# CropCircuit Customer Context Contract

Status: active internal operating standard

## Purpose

CropCircuit customer service and outreach depend on continuity. Customers and prospects should not need to repeat information already supplied.

This contract defines what an operator should preserve between interactions and how to preserve it safely.

## Privacy boundary

The public CropCircuit repository may contain:
- schemas;
- empty templates;
- synthetic examples;
- redacted patterns.

It must not contain:
- real customer email addresses;
- phone numbers;
- private files;
- payment details;
- credentials;
- customer PII;
- confidential business data;
- sensitive notes.

Real customer/prospect records belong in authorized private systems, local encrypted storage, or approved connected tools.

## Minimum contact state

For every meaningful prospect/customer relationship, preserve:

- internal contact ID;
- person / organization;
- relationship type: prospect, customer, partner, vendor, lender, other;
- source of relationship;
- current problem or goal;
- relevant CropCircuit offer/capability;
- evidence already shown;
- promises made by CropCircuit;
- promises made by the other party;
- last meaningful interaction date;
- last meaningful interaction summary;
- current status;
- blocker;
- owner;
- next action;
- next review date;
- opt-out / do-not-contact state;
- confidence / uncertainty notes;
- links to source thread or internal record.

## Status vocabulary

Use one of:

- `new_signal`
- `researching`
- `qualified`
- `contacted`
- `engaged`
- `discovery`
- `proposal_or_scope`
- `awaiting_customer`
- `awaiting_cropcircuit`
- `paid_active`
- `delivered`
- `won`
- `no_fit`
- `declined`
- `dormant`
- `do_not_contact`

Do not use `won` for verbal interest.
Do not use `paid_active` without verified external payment.

## Interaction event minimum

Every meaningful interaction should be reducible to an event with:

- timestamp;
- channel;
- direction: inbound/outbound/internal;
- actor;
- contact ID;
- short factual summary;
- customer intent / question;
- CropCircuit response;
- commitment created;
- next action;
- source/evidence reference.

## Context compression rule

Preserve what changes future behavior.

Good:
- "Prospect uses three CSV exports and manually reconciles them weekly; asked whether low-confidence rows can be reviewed before import."

Bad:
- "Had a good conversation."

## Promise ledger rule

Promises are first-class state.

Examples:
- delivery by date;
- send revised scope;
- check compatibility;
- provide sample;
- wait until prospect talks to partner;
- do not contact again before a date.

A promise must not disappear because an AI session ended.

## Uncertainty rule

Distinguish:
- customer stated;
- externally verified;
- operator inference;
- unknown.

Do not convert inference into fact in later outreach.

## Thread-read rule

Before any follow-up:
1. read the latest thread;
2. review commitments;
3. check whether the requested action already happened;
4. check opt-out state;
5. then draft.

## Handoff rule

When another AI or person takes over, they should be able to answer:
- who is this?
- what do they want?
- what did we promise?
- what is blocked?
- what happens next?
without asking the customer to reconstruct the relationship.
