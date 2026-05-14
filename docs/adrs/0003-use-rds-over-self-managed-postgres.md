# 0003 - Use AWS RDS over self-managed PostgreSQL on EC2

- **Status**: Accepted
- **Date**: 2026-05-11
- **Deciders**: Juan M. Bermúdez Escobar

## Context and Problem Statement

Cash Tracker stores financial records (cash transactions, balances, categories)
for a real client. These records are operationally critical: data loss or
unrecoverable corruption is unacceptable. The database must run on AWS and stay
within the Free Tier for the first year.

We must choose between running PostgreSQL as a containerized service on the
same EC2 host as the application, or using a managed database service.

## Decision Drivers

- Durability of financial data is non-negotiable
- AWS Free Tier compliance for year one
- Single-engineer operational capacity (minimize manual database operations)
- Recovery from human error or hardware failure must be possible at fine-grained
  points in time

## Considered Options

1. **AWS RDS for PostgreSQL (db.t3.micro)**
2. **Self-managed PostgreSQL in a Docker container on the same EC2 host**
3. **Self-managed PostgreSQL on a separate, smaller EC2 host**

## Decision Outcome

Chosen option: **AWS RDS for PostgreSQL on db.t3.micro**.

The decision is not driven by cost. In fact, **self-managed PostgreSQL on EC2
is cheaper than RDS post-Free-Tier**: RDS charges a managed-service premium
(roughly 30–50% over the equivalent EC2 + EBS cost). We accept this premium
because what RDS provides — automated backups, point-in-time recovery,
automated minor-version patching, replicated storage within an Availability
Zone, and operational separation from the application host — would otherwise
need to be built and maintained manually.

The dominant driver is **data durability and recovery**. If the application
host and the database share fate (both on the same EC2), a single failure
mode — a kernel panic, a full disk, an accidental `terraform destroy`, a
runaway log file — can take down both the application and the data at once,
with no clean recovery path beyond ad-hoc `pg_dump` cron scripts that we
would have to write, monitor, and verify ourselves.

### Pros and Cons of the Options

**Option 1 — AWS RDS**

- ✅ Automated daily backups with configurable retention (default 7 days)
- ✅ Point-in-time recovery to the second within the backup window
- ✅ Replicated storage within the AZ; durable by default
- ✅ Automated minor-version engine patches
- ✅ Operational isolation: database lifecycle is independent of EC2 lifecycle
- ✅ Free Tier covers db.t3.micro + 20 GB gp2 storage + 20 GB backup for year one
- ❌ More expensive than self-managed after the Free Tier (~$15–25/month)
- ❌ AWS lock-in for the database layer

**Option 2 — Containerized PostgreSQL on the same EC2**

- ✅ Cheaper post-Free-Tier
- ✅ No additional AWS service to learn or configure
- ❌ Shared failure domain with the application
- ❌ No backups without writing and maintaining `pg_dump` automation
- ❌ No point-in-time recovery
- ❌ Storage durability limited to a single EBS volume
- ❌ All maintenance (patches, vacuum, monitoring) is manual

**Option 3 — Self-managed PostgreSQL on a separate EC2**

- ✅ Separates failure domains
- ✅ Cheaper than RDS post-Free-Tier
- ❌ Two EC2 hosts to maintain (doubles operational surface)
- ❌ Still requires manual backup/recovery automation
- ❌ Free Tier covers only one t2.micro/t3.micro per month; second host costs
  money from day one

## Consequences

- The database is provisioned and managed via Terraform in
  `infra/terraform/rds.tf` (Phase 4)
- The database lives in a private subnet with security group rules allowing
  inbound traffic only from the application's security group
- Connection credentials are stored in AWS Secrets Manager (or SSM Parameter
  Store) and injected into the application at deploy time, never committed
- Backup retention is set to 7 days; point-in-time recovery is enabled
- Estimated monthly cost after Free Tier: ~$15–25 USD (db.t3.micro + 20 GB
  storage + 7-day backups). The client is informed of this future cost.

## Re-evaluation Trigger

Reconsider this decision if:

- Cost becomes a binding constraint and downtime/data-loss risk is acceptable
- The application is rewritten to be inherently stateless and data lives
  elsewhere (e.g., a third-party transactional system)

## Related

- ADR-0001: Use Docker Compose over Kubernetes
- AWS RDS Free Tier: <https://aws.amazon.com/free/>
