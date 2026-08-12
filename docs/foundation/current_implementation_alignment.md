# Current Implementation Alignment

This document is the source of truth for how the current repository behaves. Foundation and reference documents describe principles and target architecture, but they must not contradict the implementation notes below.

## Current Workflow States

The implemented workflow states are:

```text
created -> planning -> designing -> building -> reviewing -> testing -> awaiting_approval -> completed
```

The workflow can also enter:

- `escalated` when human intervention is required.
- `failed` when execution fails or a run is terminated.

There is no separate persisted `cancelled`, `ready_for_deployment`, `architecture`, or `implementation` state. Documentation may use those as plain-language concepts, but code and APIs use the states above.

## Current Human Gates

The current hard gates are:

- Intake approval: the user approves a validated Engineering Specification before creating a workflow.
- Escalation resolution: escalated workflows require human action to resume, restart, or terminate.
- Production approval: `awaiting_approval` requires human approval before completion, passport generation, and deployment guide generation.

There is no separate architecture sign-off gate or passport-generation approval gate in the current code. Architecture and passport artifacts are verified by workflow checks and the production approval flow.

## Current Engineering Specification Contract

The live Engineering Specification is one Markdown document with shared sections and explicit agent subsections for:

- Coordinator
- Architect
- Builder
- Reviewer
- QA
- Platform

The current required sections are defined in `app/services/specification_contract.py`.

## Current Build Plan Contract

Coordinator build plans must be Markdown with numbered phases. Each phase must include:

- Objectives
- Tasks
- Timeline
- Resources
- Deliverables

The Challenger verifies this structure before the workflow advances.

## Current Infrastructure

The implemented stack favors:

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL in production-style environments
- SQLite in tests
- OpenRouter-compatible model routing
- Docker
- Railway-oriented deployment

References to Temporal, LangGraph, Supabase, RunPod, Slack, Email, GitHub Actions, or MCP are target-state or optional integration references unless implementation code exists in the repository.

## Current Knowledge Flow

Shared Knowledge exists as a curated knowledge service and API. Platform may propose knowledge candidates. Human curation remains required before promotion.

## Current Portfolio Cleanup

Terminated projects are represented as `failed` workflows. Removing a terminated project from the portfolio is a soft hide stored in workflow artifacts; database records and generated artifacts are preserved.
