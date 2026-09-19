# CSA Share Price & Break-Even Calculator

A CSA price can be tested against the costs a farm actually wants the share program to carry.

## Inputs

- planned share count
- current/proposed share price
- fixed season costs
- season labor hours
- labor cost per hour
- variable cost per share
- payment fee percentage
- target season surplus

## Core math

```text
labor cost
  = season labor hours × labor cost per hour

season fixed cost
  = other fixed costs + labor cost

contribution per share
  = price × (1 − payment fee rate)
    − variable cost per share

break-even shares
  = ceil(season fixed cost / contribution per share)

shares needed for target surplus
  = ceil((season fixed cost + target surplus)
         / contribution per share)
```

At a fixed planned share count, the calculator can also solve for the price needed to cover all entered costs plus the target season surplus:

```text
required price
  = (season fixed cost
     + target surplus
     + planned shares × variable cost per share)
    / (planned shares × (1 − payment fee rate))
```

## Reusable implementation

See:

- `csa_math.js`
- `csa_math.test.mjs`

## Important limits

The calculator does not automatically include costs the operator leaves out.

It also does not predict:

- crop yield
- member retention
- cancellations
- production shocks
- taxes
- financing
- spoilage
- owner goals

It is a transparent first-pass unit-economics model, not a forecast.
