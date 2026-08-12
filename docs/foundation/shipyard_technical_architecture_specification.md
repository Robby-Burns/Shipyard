# Shipyard Technical Architecture Specification

> Current implementation details are governed by `current_implementation_alignment.md`. This document describes current architecture principles and target-state extension points.

## Purpose

This document defines the technical implementation of the Shipyard Engineering Organization.

The Constitution defines Shipyard's principles.
The Role Specifications define Shipyard's engineering disciplines.
This document defines the software architecture that enables those disciplines.

## System Context

Shipyard begins after an Approved Engineering Specification has been created through an external product discovery process.

Shipyard is responsible only for engineering execution.

The architecture is designed around four independent concerns:
- Workflow orchestration
- Engineering disciplines
- Model routing
- Secure tool execution

This separation allows each subsystem to evolve independently while maintaining a stable engineering organization.

## High-Level Architecture

```
Approved Engineering Specification
  |
  v
Workflow Engine
  |
  v
Engineering Disciplines
  |
  v
Model Router
  |
  v
Tool Gateway
  |
  v
Engineering Infrastructure
(GitHub * Railway * Docker * optional providers)
```

Platform continuously observes the entire system and improves organizational performance.

Shared Knowledge supports every engineering discipline.

---

## Workflow Engine

### Purpose

The Workflow Engine orchestrates the engineering disciplines defined in the Shipyard Role Specification. It manages workflow progression rather than performing engineering work.

### Responsibilities

- Start engineering workflows
- Route work between disciplines
- Track workflow state
- Enforce required approvals
- Pause execution when escalation is required
- Record workflow history

The Workflow Engine never modifies engineering artifacts.

The current Workflow Engine is implemented in application service code with database-backed workflow state. A future durable workflow runtime may support persistent execution state, pause/resume semantics, retries, recovery from failures, and long-running workflows across process restarts.

The workflow runtime is an implementation detail and may be replaced without affecting the engineering organization. Temporal, LangGraph, or equivalent technologies are target-state options, not current dependencies.

### Workflow States

A workflow progresses through deterministic lifecycle states.

- Created
- Planning
- Designing
- Building
- Reviewing
- Testing
- Awaiting Human Approval
- Escalated
- Completed
- Failed

The Workflow Engine is responsible for maintaining workflow state and ensuring deterministic transitions between states.

---

## Engineering Disciplines

Shipyard consists of six engineering disciplines.

- Coordinator
- Architect
- Builder
- Reviewer
- QA
- Platform

Their responsibilities are defined in the Shipyard Role Specifications.

The architecture treats every discipline as an interchangeable execution component.

---

## Model Router

### Purpose

Assign the most appropriate AI model for each engineering capability.

Engineering disciplines never select models directly. They request capabilities. The Model Router determines which model should perform the work.

### Selection Criteria

Model selection may consider:
- Capability
- Cost
- Context length
- Latency
- Reliability
- Organizational policy

### Routing Policies

Current and target integrations include:
- Architecture -> Best architecture model
- Coding -> Best coding model
- Code Review -> Best review model
- Testing -> Best validation model
- Analysis -> Best reasoning model

Whenever practical:
- Builder and Reviewer should use different model families.
- QA should validate work using a model different from Builder.
- Models remain interchangeable.

Routing policies may evolve without changing the engineering organization.

---

## Tool Gateway

### Purpose

The Tool Gateway is the only component permitted to access external systems and infrastructure.

Engineering disciplines never receive infrastructure credentials.

### Responsibilities

- Execute infrastructure operations
- Authenticate requests
- Enforce authorization
- Log every action
- Validate permissions
- Return execution results

### Supported Systems

Examples include:
- GitHub
- Railway
- Docker
- OpenRouter
- RunPod (target-state or optional)
- Supabase (target-state or optional)
- Email (target-state or optional)
- Slack (target-state or optional)

Additional integrations may be added without changing engineering workflows. Integrations should be modular, replaceable, and isolated behind the Tool Gateway.

The Tool Gateway exposes stable capability-based interfaces independent of the underlying communication protocol. Standardized protocols such as the Model Context Protocol (MCP) may be used where appropriate, but engineering disciplines remain isolated from protocol and provider details.

Tool integrations should be implemented using standardized invocation interfaces whenever practical. Protocols and providers are implementation details hidden behind stable Tool Gateway APIs, allowing integrations to evolve without affecting engineering disciplines.

---

## Memory Architecture

Shipyard maintains three categories of organizational knowledge.

### Private Memory

Role-specific operational context. Temporary. Not shared automatically.

### Shared Knowledge

Curated organizational knowledge. Examples include:
- Architecture Decision Records
- Coding Standards
- Reusable Components
- Testing Patterns
- Security Findings
- Performance Lessons
- Operational Playbooks

Shared Knowledge is promoted intentionally. It is never updated automatically.

### External Knowledge

Reference material and research.

External knowledge is never promoted into Shared Knowledge without human approval.

---

## Risk Engine

Every engineering task receives a declared risk classification.

- LOW
- MEDIUM
- HIGH

Risk influences:
- Review depth
- Test strategy
- Human approvals
- Deployment workflow

Engineering effort scales with implementation risk.

---

## Human Decision Gates

Shipyard pauses execution whenever human judgment is required.

Examples include:
- Ambiguous requirements
- Conflicting specifications
- Architecture changes that alter product intent
- High-risk implementation plans
- Production deployment
- Infrastructure deletion
- Permanent knowledge promotion
- Budget overrides

Human decisions resume workflow execution.

---

## Platform

Platform continuously improves the engineering organization.

Platform observes engineering execution but does not participate in feature implementation.

Platform measures:
- Engineering throughput
- Cost
- Security
- Reliability
- Review quality
- Complexity
- Model performance
- Knowledge reuse

Platform produces operational recommendations rather than engineering work.

---

## Security

Security is implemented through software rather than prompt instructions.

Engineering disciplines never receive infrastructure credentials. All infrastructure operations pass through the Tool Gateway.

Every privileged action is:
- Authenticated
- Authorized
- Logged
- Auditable

---

## Deployment

Engineering work progresses through the following implementation pipeline.

```
Approved Engineering Specification
  |
  v
Workflow Engine
  |
  v
Coordinator
  |
  v
Architect
  |
  v
Builder
  |
  v
Reviewer
  |
  v
QA
  |
  v
Release Candidate
  |
  v
Human Production Approval
  |
  v
Deploy
  |
  v
Platform
  |
  v
Shared Knowledge
```

---

## Technology

Shipyard intentionally favors a simple implementation built from proven components.

Current implementation and target integrations include:
- Python
- FastAPI
- PostgreSQL
- pgvector
- OpenRouter
- GitHub
- Docker
- Railway
- RunPod (target-state or optional)
- Supabase (target-state or optional)

Technology choices may evolve independently of the engineering organization. Additional integrations may be added without changing engineering workflows. Integrations should be modular, replaceable, and isolated behind the Tool Gateway.
