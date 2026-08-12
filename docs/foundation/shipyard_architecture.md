# Shipyard Architecture (Rarely changes)

> Current implementation details are governed by `current_implementation_alignment.md`.

## Core Principle

> **The engineering organization is permanent. Infrastructure is replaceable.**

This principle defines the invariant parts of Shipyard - the roles, workflow, and organizational learning - while allowing all underlying technologies to evolve.

---

## Engineering Intake Capability

*Purpose*: Accept engineering requests in many forms (natural‑language description, approved product specification, PRD, Jira export, existing Engineering Specification, etc.) and guide the user toward a **validated Engineering Specification**.

*Key behaviours*:
- Prompt the user for the information required to complete an Engineering Specification.
- Validate that all mandatory sections are present.
- Produce a structured specification artifact that can be persisted and later approved by a human.

---

## Workflow Engine & Engineering Roles

The **Workflow Engine** coordinates the six core engineering disciplines. When a discipline needs AI reasoning it requests a capability from the **Model Router**.

```
Coordinator -> Architect -> Builder -> Reviewer -> QA -> Platform
```

*Each discipline has a permanent responsibility; models may change, but the roles do not.*

- **Coordinator** - tracks milestones, enforces human‑approval gates, and routes work.
- **Architect** - creates system architecture, ADRs, and updates the specification with design decisions.
- **Builder** - generates code, commits to version control, and runs unit tests.
- **Reviewer** - performs code and security review against acceptance criteria.
- **QA** - executes functional, performance, and accessibility testing.
- **Platform** - observes execution, gathers evidence, and formulates improvement recommendations.

---

## Infrastructure Adapter Pattern

### Philosophy

> The pattern isolates the AI Engineering Organization from concrete technology choices. Infrastructure may evolve over time, yet the engineering roles, workflow, and organizational behavior stay invariant.

### Core Responsibilities (for every adapter)
- **Connection management** - establish and release resources.
- **Health reporting** - expose status and diagnostics.
- **Capability execution** - perform the requested operation (e.g., inference, repository push).
- **Configuration validation** - ensure the adapter is correctly set up before use.
- **Graceful shutdown** - cleanly release resources.

### Core Interface Set (conceptual, not concrete file names)
- `ModelInterface`
- `MemoryInterface`
- `RepositoryInterface`
- `DeploymentInterface`
- `StorageInterface`
- `NotificationInterface`
- `IdentityInterface`
- `SearchInterface`
- `MonitoringInterface`

Each concrete adapter implements the responsibilities above while adhering to the same logical contract.

---

## Model Family Adapters (Inference Providers)

When a role requires AI reasoning it calls the **Model Router** with a capability name such as coding, architecture, code review, testing, or general reasoning. The router selects a configured model/provider adapter.

Supported model providers are configuration-driven and replaceable. Current defaults route through OpenRouter-compatible model identifiers, with native-provider bypass support where configured.

Routing policies are defined in application configuration and model-catalog data; they are not part of this architecture description.

---

## Engineering Context Builders

**Why they exist**: To ensure each discipline receives only the information necessary to fulfill its responsibility, reducing token usage, cost, and noise while preserving clear organizational boundaries.

Each builder produces a concise context payload for its role (e.g., Builder gets the current task, relevant ADRs, coding standards; Reviewer gets the code diff and acceptance criteria).

---

## Engineering Instruction Contract

All roles communicate with the Model Router using a uniform contract that describes the request:

```
Mission
Inputs
Constraints
Context
Required Output
Done When
```

The Model Family Adapter translates this contract into the provider‑specific request format (function‑call JSON, tool syntax, etc.).

---

## Capability‑Based Routing

Roles request **capabilities**, not specific models. The Model Router resolves the request using application configuration, model catalog data, and routing outcomes.

```yaml
coding:
  primary: configured coding model
architecture:
  primary: configured architecture model
review:
  primary: configured review model
multimodal_analysis:
  primary: configured analysis model
```

---

## Status Capability

Transparency is a core requirement. Any user can query `Status` and receive a structured report of each role's state, current task, and estimated completion time.

---

## Engineering Journal & Timeline

The **Engineering Journal** records a chronological log of major events (Specification approved, Architecture completed, ADRs created, Implementation milestones, Review completed, QA passed, Deployment prepared, Passport generated). This journal is incorporated into the **Engineering Passport** as the **Engineering Timeline**, providing an audit trail and valuable hand‑off documentation.

---

## Engineering State Machine

A project progresses through well‑defined states observable via the Status capability:

```
Engineering Intake -> Validated Engineering Specification -> Approved Workflow -> Planning -> Designing -> Building -> Reviewing -> Testing -> Awaiting Approval -> Completed
```

Transitions are driven by the Workflow Engine and gated by human approvals where required. The current persisted workflow states are documented in `current_implementation_alignment.md`.

---

## Organizational Learning Loop

Shipyard improves through observation and evidence, not by modifying the AI itself.

```
Engineering Execution
    v
Observation (Platform)
    v
Evidence (metrics, recurring ADRs, repeated clarification requests, success/failure patterns)
    v
Recommendation (proposed process or template changes)
    v
Human Approval
    v
Organizational Standard (shared knowledge, updated templates, best‑practice guides)
    v
Future Projects
```

---

## Guiding Principles (Reordered for clarity)

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

*This Architecture document defines responsibilities, relationships, and invariants. Concrete implementation details (folder layout, class names, APIs) belong in the MVP Implementation Plan.*
