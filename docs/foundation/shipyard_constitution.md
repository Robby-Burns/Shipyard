# Shipyard Constitution (Immutable Principles)

> Current implementation details are governed by `current_implementation_alignment.md`.

## What is Shipyard
> **Shipyard is an AI Engineering Organization.**

It accepts engineering requests (natural‑language, approved product specifications, PRDs, Jira exports, existing Engineering Specifications) and transforms them into production‑ready software through a disciplined, transparent workflow.

## Immutable Principles
1. **Permanent Engineering Organization** - The six core roles (Coordinator, Architect, Builder, Reviewer, QA, Platform) and the workflow engine are permanent. Models and infrastructure may change, but the organization's structure does not.
2. **Infrastructure Adapter Pattern** - All external services (models, repositories, storage, deployment, monitoring) are accessed behind stable interfaces, making them replaceable without altering the organization.
3. **Engineering Knowledge Belongs to the Organization** - Decisions, architectures, and standards are documented and owned by Shipyard, not by any individual model.
4. **Human Accountability** - Humans approve critical milestones currently implemented as specification approval, escalation resolution, and production approval. Models provide recommendations only.
5. **Transparency & Status** - Every project exposes a `Status` capability that reports role state, progress, and ETA.
6. **Engineering Passport** - Every completed project must produce an Engineering Passport that records what was built, why, how, and operational guidance.

## Decision‑Making Process
- **Human Approval Gates** - Specification approval, escalation resolution, and production approval require explicit human action in the current implementation. Additional gates may be added only when they preserve this Constitution.
- **Organizational Learning Loop** - Observations -> Evidence -> Recommendations -> Human Approval -> Updated Organizational Standards.
- **Never‑Change Guarantees** - The list of core roles, the state machine, and the Constitution itself are only changed via a formal amendment process documented in the Engineering Passport.

## Governance
- **Amendments** - To modify the Constitution, a new version must be proposed, reviewed by the Architect, approved by the Coordinator, and ratified by a majority of human stakeholders.
- **Versioning** - Each amendment creates a new version `Shipyard Constitution vX.Y` stored in the repository.

---
*This document defines the immutable foundation of Shipyard. All other artifacts (Vision, Architecture, Standards, Roadmaps) evolve underneath this Constitution.*
