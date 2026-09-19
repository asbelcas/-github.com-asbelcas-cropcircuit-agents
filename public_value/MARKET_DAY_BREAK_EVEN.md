# Farmers Market Break-Even Calculator

A market can look busy and still fail to cover the time and costs the farm chooses to count.

This tool makes those assumptions explicit.

## Inputs

### Fixed / day-level costs

- booth fee
- round-trip miles
- **user-supplied** vehicle cost per mile
- travel time
- setup time
- selling time
- teardown time
- workers
- labor cost per hour
- other fixed day costs

### Per-sale economics

- average sale
- variable cost per sale
- card fee percentage
- optional expected transaction count

## Core calculation

```text
vehicle cost
  = round-trip miles × vehicle cost per mile

labor cost
  = (travel + setup + selling + teardown hours)
    × workers
    × labor cost per hour

fixed day cost
  = booth fee + vehicle cost + labor cost + other fixed costs

card fee per sale
  = average sale × card fee percentage

contribution per sale
  = average sale − variable cost per sale − card fee per sale

break-even transactions
  = ceil(fixed day cost / contribution per sale)
```

The reusable implementation is in `market_math.js`.

## Important omissions

A first-pass market-day model does not automatically capture:

- taxes
- spoilage
- unsold inventory
- weather
- long-run customer acquisition value
- strategic brand value
- production overhead not assigned to each sale
- opportunity cost beyond the labor rate entered

The purpose is transparency, not false precision.
