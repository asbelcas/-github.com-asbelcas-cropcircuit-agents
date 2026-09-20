# Automation Project Preflight

A short scoping worksheet for small data/AI automation projects.

Use it before choosing tools. The goal is to identify the smallest reliable workflow that removes real manual work.

## 1. Trigger

What starts the workflow?

- new CSV/Excel file
- form submission
- new email/attachment
- scheduled run
- webhook/API event
- manual button

## 2. Input

Describe each input source.

| Input | Format | Typical volume | Sensitive? | Example available? |
| --- | --- | ---: | --- | --- |
|  |  |  |  |  |

## 3. Required transformation

For each field or step, mark the cheapest reliable method.

| Step | Deterministic rule | Lookup/API | LLM | Human review |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

Prefer deterministic rules when they are sufficient.

## 4. Destination

Where must the result go?

- Airtable
- Google Sheets
- CRM
- database
- CSV/JSON file
- Slack/email
- another API

Record required fields, unique keys, and update-vs-create behavior.

## 5. Failure behavior

Decide this before implementation.

- What should happen when one row fails?
- What should happen when an API is unavailable?
- Which errors may retry automatically?
- Which errors require a person?
- Where are failures recorded?
- Can the run be safely replayed?

## 6. Duplicate prevention

Define an idempotency key.

Examples:
- source-system record ID
- invoice number + vendor
- normalized email + campaign ID
- file hash + row number

A second run with the same key should update/skip intentionally rather than create a silent duplicate.

## 7. AI boundary

If an LLM is used, specify:

- exact task
- expected structured output
- schema
- confidence/review rule
- deterministic checks after output
- maximum acceptable cost per record/run

Do not use an LLM merely to replace ordinary parsing or arithmetic.

## 8. Success criteria

Define measurable acceptance tests.

Examples:
- 100 sample rows processed
- zero duplicate destination records
- malformed rows isolated without crashing the batch
- required fields validated before write
- low-confidence cases routed to review
- rerun produces the same intended state
- run log identifies every input and outcome

## 9. Security

List:
- credentials required
- where secrets will live
- whether personal/health/financial data is involved
- data retention requirement
- who may access run logs

## 10. Pilot boundary

Choose the smallest useful first milestone.

A strong pilot usually has:
- one input;
- one transformation path;
- one destination;
- one exception queue;
- one replay test.

Only expand after that loop works reliably.

---

This worksheet is a reusable CropCircuit public-value asset. It is a scoping aid, not a guarantee that a particular platform or integration is supported.
