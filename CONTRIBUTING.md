# Contributing to Cash Tracker

## Workflow

1. Create a feature branch from `main`: `git checkout -b feat/short-description`
2. Make changes, commit using Conventional Commits format
3. Push branch and open a Pull Request
4. CI must pass before merge
5. Squash and merge to `main`

## Branch naming

- `feat/...` — new features
- `fix/...` — bug fixes
- `docs/...` — documentation only
- `chore/...` — tooling, dependencies, refactors with no behavior change
- `refactor/...` — code changes without behavior change

## Commit messages: Conventional Commits

This project follows [Conventional Commits 1.0.0](https://www.conventionalcommits.org/).

Format: `<type>(<scope>): <description>`

Types:

- `feat`: new feature
- `fix`: bug fix
- `docs`: documentation
- `chore`: tooling, deps, configs
- `refactor`: refactor without behavior change
- `test`: adding/updating tests
- `ci`: CI/CD changes
- `perf`: performance improvement

Examples:

- `feat(api): add expense endpoint`
- `fix(docker): correct exposed port in compose`
- `docs(adr): add ADR-0004 for Nginx choice`

Breaking changes: append `!` after type/scope: `feat(api)!: rename /expenses to /transactions`

PR title validation enforces these types via CI.

## Pull Requests

- One logical change per PR
- Link to related ADR if introducing an architectural decision
- Description: what + why (not how — code shows how)
- Self-review the diff before requesting review
- Squash and merge is the only allowed merge strategy

## Architecture Decision Records (ADRs)

Significant architectural decisions are documented as ADRs in `docs/adrs/`.

Format: numbered (`NNNN-short-title.md`), using a simplified version of the
[MADR template](https://adr.github.io/madr/).

Before adding a new ADR, check if existing ones cover the decision.

## Code style

- Python: enforced via `ruff` (added when the application code lands)
- Markdown: linted via `markdownlint-cli2` in CI; keep line width ~100 where practical
- Terraform: enforced via `terraform fmt` (added in Phase 4)

## Local development

See [README.md](README.md#quick-start-local-development).
