# Offline Equipment Checklist

This tool records **operator-defined** equipment checklists and their completion history.

It deliberately does not supply default safety or maintenance items.

## Why

Equipment checklist needs vary by:

- machine
- attachment
- operating environment
- manufacturer instructions
- applicable regulations
- employer procedures
- service history

A generic software author should not invent a safety-critical checklist and imply it is complete.

## Templates

Each template contains:

- equipment / system
- checklist name
- one or more operator-entered items

Examples of checklist categories could include startup, shutdown, cleaning, inspection, or service, but the actual items come from the farm's established guidance.

## Completion history

A saved session records:

- completion timestamp
- equipment
- checklist name
- number of boxes checked
- total checklist items
- optional meter hours
- optional issues / follow-up note

The history is a record of what the user marked.

It is **not independent verification** that a check occurred and it is not a safety certification.

## Privacy

The browser storage key is:

```text
cropcircuit_equipment_checklists_v1
```

The tool supports CSV history export and JSON backup/restore.

No server sync, account, analytics, or external library is required.
