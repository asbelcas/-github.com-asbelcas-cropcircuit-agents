# Funding Radar Integration Recipes

CropCircuit's funding radar is designed to be reused without an account or API key.

## Google Sheets

In a blank cell:

```text
=IMPORTDATA("https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.csv")
```

That pulls the public CSV into a sheet. The CSV includes status, deadlines, funding, audience, tags, source URLs, and verification metadata.

## Excel / Power Query

Use Excel's **Data → From Web** flow with:

```text
https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.csv
```

For structured JSON instead:

```text
https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.json
```

## JavaScript

```js
const url =
  "https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.json";

const radar = await fetch(url).then(r => {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
});

const open = radar.opportunities.filter(x => x.status === "open");
console.log(open);
```

## Python standard library

No third-party package is required:

```python
import json
from urllib.request import urlopen

url = (
    "https://raw.githubusercontent.com/"
    "asbelcas/-github.com-asbelcas-cropcircuit-agents/"
    "main/public_value/funding_radar.json"
)

with urlopen(url, timeout=15) as response:
    radar = json.load(response)

for item in radar["opportunities"]:
    if item["status"] == "open":
        print(item["title"], item["deadline_label"], item["source_url"])
```

## curl

```bash
curl -fsSL   https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.json
```

## Calendar clients

The public iCalendar file is:

```text
https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_deadlines.ics
```

Calendar applications that support subscribing to a remote iCalendar URL can use that address. The file contains machine-readable deadlines for currently tracked dated opportunities.

## Feed readers and agents

JSON Feed 1.1:

```text
https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_feed.json
```

JSON Schema:

```text
https://raw.githubusercontent.com/asbelcas/-github.com-asbelcas-cropcircuit-agents/main/public_value/funding_radar.schema.json
```

## Website embed

Use the zero-dependency funding widget when you want rendered cards instead of raw data:

[Funding Widget documentation](FUNDING_WIDGET.md)

## Local command line

Use `funding_query.mjs` when you want to filter a downloaded clone by county, tag, status, or upcoming deadline without building an API integration:

[Funding Query documentation](FUNDING_QUERY.md)

## Stability rule

- **Data URLs point to `main`** because funding status must stay current.
- **Code integration examples pin a commit SHA** when reproducibility matters.

Every funding record should still be verified at its linked primary source before someone acts on it.
