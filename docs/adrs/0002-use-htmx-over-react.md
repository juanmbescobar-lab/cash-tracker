# 0002 - Use HTMX over React for the frontend

- **Status**: Accepted
- **Date**: 2026-05-11
- **Deciders**: Juan M. Bermúdez Escobar

## Context and Problem Statement

Cash Tracker is a mobile-first PWA for entering cash income and expenses,
viewing balance, and visualizing categorical spending. The frontend needs to:

- Render forms and tables for CRUD on transactions
- Display Chart.js visualizations for spending breakdown
- Work offline-capable via service worker (PWA)
- Be maintained by a single backend-leaning engineer

We must choose a frontend architecture that fits the actual interaction
complexity of the application and minimizes maintenance surface.

## Decision Drivers

- The application is form-and-table driven, not a highly interactive UI
- A single engineer maintains the full stack
- Build pipeline simplicity is a primary concern
- Avoid maintaining two type systems (Python backend, TypeScript frontend)

## Considered Options

1. **HTMX + Jinja2 templates + Tailwind + Chart.js**
2. **React (SPA, e.g., with Vite + React Router)**
3. **Server-rendered Jinja2 with no client-side interactivity layer**

## Decision Outcome

Chosen option: **HTMX + Jinja2 + Tailwind + Chart.js**.

HTMX extends HTML with attributes (`hx-get`, `hx-post`, `hx-target`, etc.) that
let the server return HTML fragments in response to user interactions. These
fragments replace or augment parts of the DOM directly, without a client-side
framework. The architecture is **server-side rendering with surgical DOM
updates**, not a single-page application.

This eliminates an entire class of concerns: there is no JavaScript build
pipeline, no Node toolchain, no separate frontend type system, no client-side
state management library, no HTTP API contract to keep in sync between Python
types and TypeScript types. Everything lives in Python and Jinja2 templates.

### Pros and Cons of the Options

**Option 1 — HTMX + Jinja2**

- ✅ Single language across the stack (Python)
- ✅ No build pipeline for the frontend; no Node, no bundler, no transpiler
- ✅ One source of truth for data shape (Pydantic models)
- ✅ Page load time is fast (server renders HTML, no hydration step)
- ❌ Interactions require a network round-trip (acceptable here, see below)
- ❌ Smaller ecosystem and community vs React
- ❌ Limited to applications where server round-trips per interaction are
  acceptable

**Option 2 — React SPA**

- ✅ Industry-standard for complex interactive UIs
- ✅ Rich ecosystem (component libraries, state management, devtools)
- ❌ Requires maintaining a separate frontend toolchain
- ❌ Two type systems (Python on backend, TypeScript on frontend)
- ❌ Requires designing and versioning an HTTP API surface
- ❌ Adds bundle size, hydration cost, and client-side complexity for a UI
  that does not need any of it

**Option 3 — Plain Jinja2 (no HTMX)**

- ✅ Maximum simplicity
- ❌ Every interaction requires a full page reload, which is jarring on mobile
- ❌ Cannot deliver the PWA-like feel the client expects

## Consequences

- The frontend is rendered server-side; Chart.js is included as standalone
  JavaScript for visualizations only, not as a framework
- Every interactive update (e.g., adding a transaction, filtering a list)
  involves an HTTP round-trip to the FastAPI backend
- No `package.json`, no Node version pinning, no `npm install` in CI

## Re-evaluation Trigger

Reconsider this decision if the product requires:

- Complex client-side state (drag-and-drop reordering, in-place editing of
  large tables, real-time collaborative editing)
- Sustained sub-100ms interaction latency (would require avoiding server
  round-trips)
- Offline-first editing with conflict resolution (PWA caching alone is
  insufficient for this)

## Related

- ADR-0001: Use Docker Compose over Kubernetes
- HTMX documentation: <https://htmx.org/docs/>
