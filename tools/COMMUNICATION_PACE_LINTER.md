# Communication Pacing Linter

A deterministic pre-send control for CropCircuit external communication.

It implements a narrow, inspectable subset of the communication doctrine:
- same-day restraint for nonurgent outbound;
- recipient-cadence awareness;
- one-primary-next-step preference;
- low-value follow-up detection;
- message-length / question-load review;
- PACE metadata gates: Purpose, Attention, Context, Ease.

It **does not** determine whether a message is truthful, empathetic, legally appropriate, or relationship-safe. Human/agent judgment and the full message QA still apply.

## Input

Pipe a JSON object to `tools/communication_pace_linter.py`.

Example:

```json
{
  "message": "Hi Sam, the revised scope is ready. No action is needed unless you see an issue.",
  "purpose": "Deliver the revised scope.",
  "attention_reason": "A promised deliverable is ready.",
  "context_read": true,
  "next_step_count": 0,
  "hours_since_last_outbound": 5,
  "recipient_average_reply_hours": 24,
  "responding_to_inbound": false,
  "material_update": true,
  "urgent": false
}
```

## Output

The tool emits:
- `PASS`: no deterministic pacing/load flag found;
- `REVIEW`: likely cognitive-load or tone-pressure issue to inspect;
- `HOLD`: deterministic rule says do not send yet.

A `PASS` is **not authorization to send**. It only means this linter found no configured pacing blocker.

## Design principle

> AI speed must never become human pressure.
