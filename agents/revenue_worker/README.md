# Autonomous Revenue Worker

Purpose: let the AI operator discover and execute **AI-native paid work** without using Casey's time as the product.

## Operating rule

Casey is the owner/beneficiary. The agent is the worker.

Human labor (surveys, interviews, juries, focus groups, manual freelancing) is not the default revenue source.

## Supported market classes

- agent-native bounty markets
- coding/documentation/data/research bounties
- zero-upfront public-data tasks
- proof-based digital deliverables
- legitimate refunds/recoveries handled by the operator

## Safety / financial constraints

- zero-spend by default;
- no leverage, trading, gambling, or prediction markets;
- no task that requires a deposit, bond, gas, subscription, or entry fee unless specifically authorized;
- no fabricated proof or eligibility;
- no unauthorized security testing;
- no private keys or seed phrases in source/config;
- payout credentials are public addresses or platform API keys only, supplied through deployment secrets.

## Architecture

`worker.py`:
1. reads public opportunity feeds;
2. normalizes opportunities;
3. rejects human-labor and pay-to-play tasks;
4. scores by expected value, execution fit, funding evidence, and competition;
5. emits a machine-readable candidate queue;
6. write/claim operations remain disabled unless the relevant environment credential is present.

This repository contains no payout secret, wallet private key, or platform API key.
