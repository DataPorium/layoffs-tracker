# US layoffs tracker in Python: layoffs by company, state and industry to CSV

Download every US layoff for a company, a state, an industry or a date range, and rank the companies with the most workers affected. Each layoff comes from state layoff notices, SEC filings and news reports, joined into one record so it is never counted twice.

```bash
python layoffs_tracker.py --state CA --since 2026-01-01
python layoffs_tracker.py --company intel
python layoffs_tracker.py --top --days 90
```

## Quick start

```bash
git clone https://github.com/DataPorium/layoffs-tracker.git
cd layoffs-tracker
pip install -r requirements.txt
export DATAPORIUM_API_KEY="YOUR_API_KEY"
python layoffs_tracker.py --state TX --min-workers 100
```

It writes `output/layoffs.csv` with one row per layoff: announced and effective date, company, ticker, state, county, city, industry, workers, share of the workforce, type, status and sources. It also prints the companies with the most workers in your selection.

With `--top` it writes `output/top_companies.csv` instead: companies ranked by workers affected over the last 30, 90 or 365 days, or all time.

## Options

| Option | Meaning |
|---|---|
| `--state CA,TX` | One or more states |
| `--company intel` / `--ticker INTC` | One company |
| `--naics 51` | Industry code prefix, for example `51` (information) or `31-33` (manufacturing) |
| `--since 2026-01` / `--until 2026-06-30` | Announced date range |
| `--min-workers 100` | Only layoffs of at least this many workers |
| `--status confirmed` | `confirmed` (default): an official notice or filing exists. `reported`: news only. `all`: both |
| `--max 1000` | Most layoffs to download (default 1000) |
| `--top --days 90` | Rank companies over 30, 90 (default), 365 or 0 (all time) days |

Workers are counted only when a source states them, so some layoffs have no number. The default `confirmed` keeps out news-only reports, whose numbers are less reliable.

## How it works

Two endpoints of the DataPorium API, through the [Python library](https://github.com/DataPorium/dataporium-python):

```python
from dataporium import DataPorium

dp = DataPorium()
events = dp.layoffs_events(state="CA", date_from="2026-01-01", status="confirmed", limit=200)
top = dp.layoffs_companies(days=90, sort="workers")
```

`layoffs_events` returns up to 200 layoffs per page; the script follows the pages with `offset`. The [layoffs API page](https://dataporium.tech/api-docs/layoffs-api) describes every field.

## Get an API key

The script uses the [DataPorium](https://dataporium.tech) financial data API with your own API key. Sign up at [dataporium.tech](https://dataporium.tech/pricing) and subscribe to the Premium plan; the key is in your account settings. Then set it once in your terminal:

```bash
export DATAPORIUM_API_KEY="YOUR_API_KEY"     # macOS and Linux
setx DATAPORIUM_API_KEY "YOUR_API_KEY"       # Windows (open a new terminal afterwards)
```

Keep the key out of code you commit or share.

## More

- Python library used here: [dataporium-python](https://github.com/DataPorium/dataporium-python)
- JavaScript and TypeScript: [dataporium-js](https://github.com/DataPorium/dataporium-js)
- Examples in curl, R, Google Sheets and Excel: [financial-data-api](https://github.com/DataPorium/financial-data-api)
- Use the same data in Claude, ChatGPT or Cursor: [dataporium-mcp](https://github.com/DataPorium/dataporium-mcp)
- API documentation: <https://dataporium.tech/api-docs>

## License

MIT. Use of the API and its data is governed by the DataPorium [Terms of Use](https://dataporium.tech/terms-of-use). Data is for information only and is not investment advice.
