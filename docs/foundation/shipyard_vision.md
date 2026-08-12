# Shipyard Vision (Never changes)

> Current implementation details are governed by `current_implementation_alignment.md`.

## Tagline
> **From engineering intent to production-ready software.**

## Mission

> **Shipyard is an AI Engineering Organization.**

Shipyard accepts engineering requests in many forms-from natural language to approved product specifications-and transforms them into production‑ready software through a disciplined engineering workflow. Shipyard performs engineering intake, creates a validated Engineering Specification, coordinates specialized AI engineering disciplines, continuously improves through organizational learning, and delivers both production‑ready software and an Engineering Passport that **explains** what was built, why it was built, how it works, and how it should be operated.

## Product Boundary

- **Atlas** answers: *"Should we build this"* (product discovery).
- **Shipyard** answers: *"Now let's engineer it."* (engineering execution).
- **Shipyard begins after product discovery is complete.** If a validated Engineering Specification does not exist, Shipyard performs engineering intake to create one from approved product documentation or user‑provided engineering requirements.
- Shipyard never performs product discovery, strategy, prioritization, market validation, or customer research. Those remain in Atlas.

## User Experience

The user starts through a minimal chat interface:

```
Welcome to Shipyard

What would you like to engineer

1. Describe an engineering problem or provide engineering documentation
2. Upload documentation (PRD, Jira export, existing Engineering Specification, etc.)
```

The system guides the user toward a **validated Engineering Specification**. Operational panels expose project status, journal entries, passports, shared knowledge, and infrastructure health without requiring users to coordinate individual roles. **Once approved, Shipyard behaves like a professional engineering organization-keeping the user informed, requesting decisions at implemented gates, and executing the engineering workflow within those gates.**

## AI Engineering Organization

Once the Engineering Specification is approved, Shipyard runs the workflow:

```
Coordinator -> Architect -> Builder -> Reviewer -> QA -> Platform
```

**Each engineering discipline has a permanent responsibility. Models may change, but engineering roles do not.**

Users never coordinate individual roles; Shipyard does.

## Engineering Passport (Required Deliverable)

Every completed project must produce an Engineering Passport containing:

- **Executive Summary** - plain‑English overview.
- **What Was Built** - capabilities, not source files.
- **Architecture** - pattern, major components, request flow, repository tour.
- **Technology Stack** - backend, frontend, infrastructure, database, authentication, testing, CI/CD.
- **Engineering Decisions** - decision, rationale, alternatives, trade‑offs.
- **AI Engineering Summary** - contributions of Coordinator, Architect, Builder, Reviewer, QA, Platform.
- **Deployment Guide** - steps, env vars, infrastructure, ops checklist.
- **External Dependencies** - APIs, databases, third‑party services, required secrets.
- **Quality Summary** - coverage, security, performance, accessibility.
- **Risks** - technical debt, known limitations, future improvements.
- **Knowledge Created** - ADRs, lessons learned, candidate knowledge, reusable components.
- **Explain This Project** - automatically generated explanations for executives, product managers, engineering managers, developers, security teams, and customers.
- **Engineering Timeline** - chronological log of major engineering events (Specification approved, Architecture completed, ADRs created, Implementation milestones, Review completed, QA passed, Deployment prepared, Passport generated).

## Guiding Principles

1. **Shipyard is an AI Engineering Organization-not an AI coding assistant.**
2. **Shipyard begins where product discovery ends.**
3. **Shipyard performs engineering intake, not product discovery.**
4. **Engineering knowledge belongs to the organization-not the model.**
5. **Models are infrastructure-not the architecture.**
6. **Infrastructure should be replaceable behind stable interfaces.**
7. **Shipyard accepts many forms of product documentation but always engineers from a validated Engineering Specification.**
8. **Every feature should strengthen the experience of working with a professional engineering organization.**
9. **Every completed project must produce an Engineering Passport.**
10. **Shipyard continuously improves through observation, measurement, recommendation, human approval, and shared organizational knowledge.**
11. **Complexity must eliminate more complexity than it introduces.**
12. **Humans remain accountable for engineering decisions.**

---
