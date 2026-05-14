# Cash Tracker

> A mobile-first PWA for tracking cash transactions, built with FastAPI + HTMX
> and deployed on AWS via Terraform.

## Overview

Cash Tracker is a self-hosted personal cash flow tracker designed for users who
deal in physical currency and need to record income and expenses from their
phone, with month-over-month balance carry-over and category breakdowns.

This repository is also a portfolio piece documenting an end-to-end DevOps
workflow: containerization, infrastructure as code, CI/CD, observability,
and a documented decision trail.

## Live Demo

> _TBD — deployed in Phase 5 of the roadmap._

## Architecture

> _Architecture diagram (Mermaid) added in Phase 2 once the Docker Compose
> topology is finalized._

The system runs as a set of containers on a single AWS EC2 instance, fronted by
Nginx with TLS via Let's Encrypt, with PostgreSQL on AWS RDS, and observability
provided by a self-hosted Prometheus + Grafana stack.

## Tech Stack

| Component         | Technology                | Why                                                      | ADR     |
|-------------------|---------------------------|----------------------------------------------------------|---------|
| Web framework     | FastAPI (Python 3.12)     | Async, type-hints, auto OpenAPI docs                     | —       |
| Frontend          | HTMX + Tailwind + Chart.js| Server-rendered, single-language stack                   | ADR-0002|
| Templates         | Jinja2                    | Native FastAPI integration                               | ADR-0002|
| Database          | PostgreSQL on AWS RDS     | Managed durability, automated backups, PITR              | ADR-0003|
| Container runtime | Docker + Docker Compose   | Single-host fit, right-sized orchestration               | ADR-0001|
| Infra as Code     | Terraform                 | Reproducible AWS provisioning, S3-backed state           | —       |
| Reverse proxy     | Nginx + Let's Encrypt     | TLS termination, single entry point                      | —       |
| Observability     | Prometheus + Grafana      | Self-hosted metrics and dashboards                       | —       |
| CI/CD             | GitHub Actions            | Native integration, free for public repos                | —       |
| Hosting           | AWS EC2 t3.micro          | Within Free Tier for year one                            | —       |

## Quick Start (Local Development)

> _TBD — local Docker Compose setup is added in Phase 2._

The intended developer experience is `docker compose up` and the application
is accessible at `http://localhost:8000`.

## Project Structure

```
cash-tracker/
├── .github/             # GitHub Actions workflows, issue and PR templates
├── .vscode/             # Editor recommendations (not enforced)
├── docs/                # ADRs and project documentation
│   └── adrs/            # Architecture Decision Records
├── CONTRIBUTING.md      # Workflow, conventions, commit format
├── LICENSE              # MIT
└── README.md            # This file
```

As the project progresses through its phases, additional directories will be
introduced organically:

- `app/` — FastAPI application (Phase 1)
- `tests/` — pytest suite (Phase 1)
- `infra/docker/` — Dockerfile and Compose files (Phase 2)
- `infra/terraform/` — Terraform modules for AWS infrastructure (Phase 4)
- `scripts/` — development and operational helpers

## Roadmap

| Phase | Scope                                                                | Status         |
|-------|----------------------------------------------------------------------|----------------|
| 0     | Repository setup, conventions, CI scaffolding                        | 🚧 In progress |
| 1     | FastAPI backend, models, CRUD endpoints, pytest                      | ⏳ Pending     |
| 2     | Dockerfile, Docker Compose for local dev, CI Docker build            | ⏳ Pending     |
| 3     | HTMX + Tailwind frontend, PWA (service worker, manifest)             | ⏳ Pending     |
| 4     | Terraform fundamentals, then VPC + EC2 + RDS + Route 53 provisioning | ⏳ Pending     |
| 5     | Manual end-to-end deploy to AWS                                      | ⏳ Pending     |
| 6     | GitHub Actions CD: image push to ECR, SSH deploy, rollback strategy  | ⏳ Pending     |
| 7     | Nginx + Let's Encrypt for HTTPS                                      | ⏳ Pending     |
| 8     | Prometheus + Grafana observability stack                             | ⏳ Pending     |
| 9     | Polish: diagrams, screenshots, demo video, methodology doc           | ⏳ Pending     |

## Development Methodology

This project follows an AI-augmented development workflow: architectural
decisions are made through in-depth discussion with an LLM assistant, every
significant decision is documented as an ADR, and implementation is delegated
to a code-execution agent with reviewed prompts. The goal is to produce a
codebase whose quality and rigor are demonstrably above what a solo engineer
would normally maintain in spare time.

A full write-up of the methodology will be added in `docs/methodology.md` at
project completion (Phase 9).

## Architecture Decisions

All non-trivial architectural decisions are documented as ADRs in
[`docs/adrs/`](docs/adrs/), following a simplified MADR format.

Current ADRs:

- [ADR-0001](docs/adrs/0001-use-docker-compose-over-kubernetes.md) —
  Use Docker Compose over Kubernetes
- [ADR-0002](docs/adrs/0002-use-htmx-over-react.md) — Use HTMX over React
- [ADR-0003](docs/adrs/0003-use-rds-over-self-managed-postgres.md) —
  Use AWS RDS over self-managed PostgreSQL

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for workflow, branching, and commit
conventions.

## License

[MIT](LICENSE) © Juan Manuel Bermúdez Escobar

## Author

Juan Manuel Bermúdez Escobar —
[LinkedIn](https://www.linkedin.com/in/juan-manuel-berm%C3%BAdez-escobar-514a24206) ·
[GitHub](https://github.com/juanmbescobar-lab)
