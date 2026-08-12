# Updated Shipyard Implementation Plan

## Goal
Create a concrete roadmap for building the Shipyard AI Engineering Organization, now anchored by the three permanent documents (Constitution, Vision, Architecture) and a clear repository layout.

## Status

This file is a historical implementation plan for the current MVP. Current runtime behavior is governed by `../foundation/current_implementation_alignment.md`.

## Engineering Decisions & Clarifications
* **Engineering Standards Directory:** Created under `docs/standards/` to hold templates and guidelines.
* **Roadmap Structure:** Adopted a flat structure within `docs/roadmap/` for ease of navigation.
* **Additional Permanent Artifacts:** Created a standardized `adr_template.md` to enforce documentation conventions.

## Proposed Changes

### Repository Layout (new files/folders)

#### `docs/foundation/shipyard_constitution.md`
*Immutable principles and governance.*

#### `docs/foundation/shipyard_vision.md`
*Product vision and experience (already created as a permanent artifact, now copied into the repo for source control).*

#### `docs/foundation/shipyard_architecture.md`
*Core architecture description (moved from the internal artifact to the repository for versioning).*

#### `docs/roadmap/implementation_plan_v2.md`
*This updated implementation plan (the file you are reading).*

#### `docs/standards/README.md`
*Placeholder for future engineering standards, templates, and ADRs.*

---

### Phase 0 - Engineering Organization Foundation [COMPLETED]
- Implement the **Workflow Engine** with the six permanent roles.
- Build the **Human‑Approval Gate** mechanism.
- Create the **State Machine** reflecting the lifecycle defined in the Architecture.
- Add **Status** capability exposing role progress.
- Wire up the **Infrastructure Adapter Pattern** with stub adapters for Model, Repository, and Deployment interfaces.

### Phase 1 - Engineering Intake Capability [COMPLETED]
- Develop the chat interface for intake (welcome flow, document upload).
- Implement validation of the Engineering Specification sections.
- Persist the specification as an artifact in `artifacts/specifications/`.

### Phase 2 - Architecture Generation [COMPLETED]
- Implement the **Architect** role to produce system diagrams and ADRs.
- Store generated architecture artifacts under `artifacts/architecture/`.

### Phase 3 - Builder & Reviewer [COMPLETED]
- Builder generates code, commits to a Git repository, and runs unit tests.
- Reviewer runs automated code‑review checks and security scans.

### Phase 4 - QA & Platform [COMPLETED]
- QA executes functional, performance, and accessibility tests.
- Platform gathers metrics, produces improvement recommendations, and logs them to the Engineering Journal.

### Phase 5 - Engineering Passport Generation & Release [COMPLETED]
- Collate all artifacts into a polished Engineering Passport markdown file.
- Provide a deployment guide and hand‑off checklist.

## Verification Plan

### Automated Tests
- Unit tests for each role's core functions.
- Integration tests for the Workflow Engine state transitions.
- End‑to‑end test simulating a full project from intake to Passport generation.

### Manual Verification
- Run a sample engineering request through the chat UI and confirm the creation of a validated Engineering Specification.
- Inspect generated Architecture diagrams and ADRs for completeness.
- Review the final Engineering Passport for required sections.
