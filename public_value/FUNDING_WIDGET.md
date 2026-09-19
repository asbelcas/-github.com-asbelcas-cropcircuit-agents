# Embeddable Michigan Farm Funding Radar

This widget lets another farm, nonprofit, extension-style resource page, or local-food website display CropCircuit's source-linked funding radar with one script tag.

It is intentionally read-only and contains no tracking code.

## Quick embed

```html
<div
  data-cropcircuit-funding-radar
  data-status="open,continuous,watch"
  data-count="6">
</div>

<script src="https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/funding_widget.js"></script>
```

## Filter to a Michigan county

County-scoped opportunities are shown only when the county matches. Statewide programs are still shown.

```html
<div
  data-cropcircuit-funding-radar
  data-county="Kalamazoo"
  data-status="open,continuous"
  data-count="8">
</div>
<script src="https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/funding_widget.js"></script>
```

## Filter by tags

```html
<div
  data-cropcircuit-funding-radar
  data-tags="regenerative agriculture,soil health"
  data-status="open,continuous,watch">
</div>
<script src="https://cdn.jsdelivr.net/gh/asbelcas/-github.com-asbelcas-cropcircuit-agents@main/public_value/funding_widget.js"></script>
```

## Options

| Attribute | Meaning |
| --- | --- |
| `data-status` | Comma-separated statuses: `open`, `continuous`, `watch`, `paused`, `closed` |
| `data-county` | Michigan county name |
| `data-tags` | Comma-separated exact tags |
| `data-count` | Maximum cards, 1–25 |
| `data-compact="true"` | Hides summaries |
| `data-theme="dark"` | Uses dark styling |
| `data-source` | Optional alternate compatible JSON source |

## Privacy and dependencies

- No analytics.
- No cookies.
- No account.
- No third-party JavaScript dependencies.
- The widget fetches only the public funding JSON unless you provide another source.

Program details can change after publication, so each card links directly to the primary program source.
