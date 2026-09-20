# Local Service Order Ledger

The service-order ledger is an operator-side local record for CropCircuit's paid implementation work.

It exists to keep the revenue story honest.

## Storage

Browser key:

```text
cropcircuit_service_order_ledger_v1
```

No central server or analytics are required.

## Minimal identifiers

Use the random intake request ID rather than unnecessary customer personal information.

Example:

```text
DS-20260920-A1B2C3D4
```

## States

Suggested statuses:

- inquiry
- scoped
- payment pending
- paid
- in progress
- delivered
- closed - no sale
- refunded

## Financial separation

The ledger displays separate values for:

### Quoted open pipeline

A quote is **not revenue**.

### Confirmed external payments

Count only when an external customer's payment is actually confirmed.

Do not mark internal transfers, payment links, clicks, or verbal commitments as confirmed payment.

### Confirmed + delivered

This is a stricter operational metric: confirmed external payment attached to work marked delivered.

### Refunds

Refunds are recorded separately and reduce net confirmed amounts.

## Privacy

The ledger does not need client names, farm names, addresses, or private farm files.

Keep identity/contact information in the communication channel that actually needs it.

## Backup

CSV export is useful for simple accounting reconciliation.

JSON export preserves the local ledger structure for restore.
