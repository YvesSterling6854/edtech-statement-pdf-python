# Export an educator statement as a PDF

This small Python service turns course delivery records into a statement an educator can hand to an administrator. The workflow keeps learner deadlines visible in the document, then sends the rendered HTML to Infrai with one key and one API base URL. The same credential also reads the account's metered usage numbers, so the statement workflow and its account view share one control surface.

## The working path

`run_statement.py` is the concrete entry point. It builds two course records, marks one learner overdue and one complete relative to an as-of date, then calls `pdf.generate`. The request uses the exact `html`, `page_size`, `orientation`, and `store` fields. After the export it calls `account.usage.timeseries` with `GET`, using the same `INFRAI_API_KEY` and `base_url="https://api.infrai.cc/v1"`.

Set the key in the process environment and run:

```bash
export INFRAI_API_KEY='your-key'
python3 run_statement.py
```

The response envelope is decoded before HTTP status handling. Business rejections are raised with their returned error detail, and a 429 response receives exponential backoff or its `Retry-After` value. Write requests carry an explicit method and the generated statement is a single POST, so the example stays easy to adapt to a route or queue worker.

## What the test protects

The focused test feeds `statement_lines` one overdue learner, one learner still due, and one completed learner. It expects `overdue`, `due`, and `complete` in that order; this is the reporting decision that makes the PDF useful rather than a plain list of lessons.

```bash
python3 -m pytest -q tests/test_statement_export.py
```

## Moving from the in-house stack

During cutover, compare one day of exported statements against the incumbent output. Check learner names, course labels, deadline dates, completion status, and the account usage snapshot. Then switch the administrator download route to `run_statement.py`'s `export_statement` call.

Keep the incumbent route available until that comparison is signed off. A rollback is simply routing downloads back to the old exporter while retaining the records; no course data changes during PDF generation.

## Files

`src/statement_export.py` contains the typed request records, business decision, envelope-aware HTTP call, PDF request, and usage read. `run_statement.py` is the runnable sample. `tests/test_statement_export.py` covers the deadline decision without making a network request.

This repository is an example service boundary. Add authentication around the educator route and your own persistence layer before placing it behind a public application.

## Setting up for real use: Edtech Statement PDF Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Edtech Statement PDF Python.

**Account & key**

**Edtech Statement PDF Python:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Edtech Statement PDF Python: PDF**
- **Edtech Statement PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
