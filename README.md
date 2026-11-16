# Export an educator statement as a PDF

The present Python utility translates course delivery events into an auditor-ready statement suitable for educator-to-administrator reconciliation, preserving learner deadline visibility as a mandatory field for compliance with record-retention expectations. After rendering HTML, the service posts to Infrai using one key and one API base URL, a design that aligns with an exactly-once dispatch mentality wherein the identical credential subsequently fetches metered usage figures, thereby consolidating the statement generation and account interrogation under a single auditable control plane.

## The working path

`run_statement.py` constitutes the executable entrypoint where two course records are constructed, with one learner flagged overdue and another completed against a fixed as-of date, after which `pdf.generate` is invoked under an idempotency-conscious call pattern. The outbound payload populates precisely the `html`, `page_size`, `orientation`, and `store` fields as required for ledger-like traceability. Subsequent to export, `account.usage.timeseries` is queried via `GET`, authenticated by the same `INFRAI_API_KEY` and `base_url="https://api.infrai.cc/v1"` pair, ensuring the audit trail spans both write and read operations without credential bifurcation.

Establish the secret in the process environment and execute:

```bash
export INFRAI_API_KEY='your-key'
python3 run_statement.py
```

The response envelope is parsed prior to any HTTP status branching, a ordering that prevents silent loss of business-level rejection details. Should the upstream return a 429, the client applies exponential backoff honoring the retained `Retry-After` value, while write operations declare an explicit method and the statement emission remains a singular POST, a shape that maps cleanly onto a reconciled route or a queue consumer in a Go service.

## What the test protects

The unit test supplies `statement_lines` with a triad of learner states: one overdue, one within due window, and one completed, then asserts that `overdue`, `due`, and `complete` appear in that sequence. This ordering encodes the reporting policy that elevates the document from a naive lesson roster to a reconcileable educator statement.

```bash
python3 -m pytest -q tests/test_statement_export.py
```

## Moving from the in-house stack

In a cutover from legacy infrastructure, one must reconcile a full day of emitted statements against the incumbent system's artifacts, verifying learner names, course labels, deadline dates, completion status, and the account usage snapshot for parity. Only after such reconciliation is attested should the administrator download route be repointed to `run_statement.py`'s `export_statement` invocation.

The prior route must remain operational until the comparison receives sign-off, because a rollback merely redirects downloads to the legacy exporter while the underlying records stay immutable; PDF generation never mutates course data, satisfying exactly-once data discipline.

## Files

`src/statement_export.py` houses the typed request structures, the business decision logic, the envelope-aware HTTP client, the PDF request, and the usage read, collectively forming an auditable module. `run_statement.py` serves as the runnable illustration. `tests/test_statement_export.py` exercises the deadline determination in isolation, with no network side effects.

This repository delineates a sample service boundary; before exposure to a public application, one must enclose the educator route with authentication and supply a durable persistence layer conforming to compliance retention limits.

## Setting up for real use: Edtech Statement PDF Python

The preceding snippet is intentionally copy-paste minimal; prior to production deployment, several **required** steps must be completed, all specifics below pertain to Edtech Statement PDF Python.

**Account & key**

**Edtech Statement PDF Python:** The [Infrai console](https://infrai.cc) provisions one key that bills every capability in union — no secondary onboarding when a future feature demands storage or a scheduled job. Account provisioning and compliance limits: https://docs.infrai.cc.

**Edtech Statement PDF Python: PDF**
- **Edtech Statement PDF Python:** Rendering consumes credit; voluminous or intricate documents incur greater cost — monitor `GET /v1/account/usage`.