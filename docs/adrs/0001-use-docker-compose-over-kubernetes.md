# 0001 - Use Docker Compose over Kubernetes for container orchestration

- **Status**: Accepted
- **Date**: 2026-05-11
- **Deciders**: Juan M. Bermúdez Escobar

## Context and Problem Statement

Cash Tracker is a single-user PWA designed to track cash transactions for one
client. The expected workload is approximately 10–50 transactions per day,
served from a single AWS EC2 t3.micro instance, with a single PostgreSQL
database (AWS RDS).

Container orchestration is needed to run the FastAPI application, the reverse
proxy (Nginx), and the observability stack (Prometheus + Grafana). We must
choose an orchestrator that fits the scale, operational simplicity, and cost
constraints of the project (AWS Free Tier).

## Decision Drivers

- System scale: single-host, single-user, low traffic
- Operational simplicity: maintained by a single engineer in spare time
- Cost: must stay within AWS Free Tier for the first year
- Portfolio value: decisions must demonstrate technical judgment, not
  resume-driven engineering

## Considered Options

1. **Docker Compose on a single EC2**
2. **Kubernetes (self-managed, e.g., k3s on EC2)**
3. **Amazon EKS (managed Kubernetes)**

## Decision Outcome

Chosen option: **Docker Compose on a single EC2**.

Kubernetes — in any form — exists to solve problems of multi-node orchestration:
horizontal autoscaling, distributed self-healing, rolling deployments without
downtime, service mesh, and node-level failure recovery. None of these problems
exist in a single-host, single-user system with predictable, low traffic.

Docker Compose provides everything we actually need: declarative multi-container
configuration, internal networking between services, volume management, and
straightforward lifecycle commands (`docker compose up`, `down`, `logs`). It is
the right-sized tool for the system.

### Pros and Cons of the Options

**Option 1 — Docker Compose**

- ✅ Operational footprint matches the team size (one engineer)
- ✅ Zero control plane overhead (no etcd, no API server, no kubelet)
- ✅ Identical commands in local dev and production EC2
- ✅ Fits AWS Free Tier (single t3.micro)
- ❌ No native multi-host scaling (acceptable trade-off, see Consequences)
- ❌ No built-in self-healing across nodes (single host, not applicable)

**Option 2 — Kubernetes self-managed (k3s)**

- ✅ Industry-standard skill
- ❌ Requires running and maintaining the control plane (additional CPU/RAM
  budget that t3.micro cannot afford comfortably)
- ❌ Adds concepts (Pods, Deployments, Services, Ingress) that provide zero
  value at this scale
- ❌ Operational complexity disproportionate to the problem

**Option 3 — Amazon EKS**

- ✅ Fully managed control plane
- ❌ ~$73/month for the control plane alone, regardless of workload
- ❌ Hard-violates the Free Tier constraint
- ❌ Same complexity surface as Option 2 from the developer's perspective

## Consequences

- The application runs as a set of containers on a single EC2 host. If the host
  fails, the application is unavailable until restored.
- Horizontal scaling beyond one host is not supported with this setup. A future
  migration to container orchestration (ECS, EKS, or Nomad) would be required
  if scale grows.
- Deployment is performed via `docker compose pull && docker compose up -d` over
  SSH, automated by GitHub Actions (see Phase 6 of the project roadmap).

## Re-evaluation Trigger

Reconsider this decision if **any** of the following becomes true:

- The system needs to run on more than one EC2 instance for the same service
- Sustained request rate exceeds ~100 requests/second
- Multi-tenancy is introduced (more than one client using the same deployment)
- Downtime tolerance becomes stricter than "minutes during deployment"

## Related

- Project requirement: AWS Free Tier compliance
- ADR-0003: Use AWS RDS over self-managed Postgres
