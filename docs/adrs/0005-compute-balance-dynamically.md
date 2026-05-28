# 0005 - Compute balance dynamically rather than store it

- **Status**: Accepted
- **Date**: 2026-05-27
- **Deciders**: Juan M. Bermúdez Escobar

## Context and Problem Statement

The application must report monthly balances: total income, total
expense, net result, a running balance carried month over month, and
an expense breakdown by category. These figures derive entirely from
the transactions already stored. We must decide whether to store these
aggregates (for example, a row per month in a ``monthly_balance``
table) or to compute them on demand from the transactions.

## Decision Drivers

- Correctness: reported balances must always match the underlying
  transactions
- Simplicity: avoid synchronization logic between transactions and
  derived aggregates
- Performance at the project's scale (tens of transactions per day,
  thousands per year)

## Considered Options

1. **Compute balances dynamically from transactions on each request**
2. **Store precomputed monthly aggregates, updated on every write**

## Decision Outcome

Chosen option: **compute balances dynamically**.

At the expected data volume (roughly 1,500 transactions per year), SQL
aggregate queries (``SUM``, ``GROUP BY``) over indexed columns return
in single-digit milliseconds. There is no performance justification for
maintaining a second, derived copy of the data.

Storing aggregates would introduce a second source of truth. Every
transaction insert, update, or delete would need to update the relevant
monthly aggregate, and any bug in that update path would silently
desynchronize reported balances from reality. For financial data, that
risk is unacceptable relative to the negligible performance gain.

### Pros and Cons of the Options

#### Option 1 — Compute dynamically (chosen)

- ✅ Single source of truth: balances always match transactions
- ✅ No synchronization code to write, test, or debug
- ✅ Fast enough at this scale (indexed SQL aggregates)
- ❌ Recomputed on every request (irrelevant at this volume)

#### Option 2 — Store precomputed aggregates

- ✅ Constant-time reads regardless of transaction count
- ❌ Two sources of truth, requiring synchronization on every write
- ❌ Any sync bug silently corrupts reported financial figures
- ❌ More code: triggers or application-level update logic
- ❌ Premature optimization at this scale

## Consequences

- Balance figures are produced by ``app/balance/service.py`` using SQL
  aggregate queries against the ``transactions`` table.
- The ``transactions.date`` index supports efficient range filtering
  for monthly and running-balance queries.
- No ``monthly_balance`` table exists; there is nothing to migrate or
  keep in sync.

## Re-evaluation Trigger

Reconsider this decision if:

- Transaction volume grows by several orders of magnitude (millions of
  rows), making per-request aggregation noticeably slow.
- Balance queries become a measured performance bottleneck under real
  usage, justifying a materialized view or cached aggregate.
