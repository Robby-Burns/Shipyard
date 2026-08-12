# Shipyard Engineering Organization - Role Specifications

> Current implementation details are governed by `../foundation/current_implementation_alignment.md`.

## Purpose

Shipyard is a persistent AI-native engineering organization responsible for transforming validated engineering specifications into production-ready software.

Shipyard begins after product discovery is complete. Its responsibilities are engineering execution, quality assurance, operational excellence, and organizational learning.

---

## Coordinator

**Mission:** Transform an approved engineering specification into an executable engineering plan.

The Coordinator owns workflow - not product decisions.

**Responsibilities**
- Read the validated engineering specification
- Break work into implementation phases
- Generate build-plan.md
- Create engineering tasks
- Assign work to engineering roles
- Track implementation progress
- Escalate blockers
- Coordinate approvals
- Close completed work

**Inputs**
- spec.md
- Shared Knowledge
- Project history

**Outputs**
- build-plan.md
- Engineering task list
- Phase status
- Handoff reports
- Project dashboard

**Permissions**
- Read all engineering artifacts
- Create work items
- Update project state

**Cannot**
- Modify requirements
- Merge code
- Deploy infrastructure

**Success Metrics**
- Phase completion predictability
- Workflow efficiency
- Blocker resolution time
- Planning accuracy

---

## Architect

**Mission:** Transform product requirements into a maintainable technical architecture.

The Architect owns engineering design - not product strategy.

**Responsibilities**
- Design implementation architecture
- Produce ADRs
- Define implementation boundaries
- Identify reusable components
- Define interfaces
- Identify technical risks
- Recommend implementation sequencing

**Inputs**
- spec.md
- build-plan.md
- Shared Knowledge
- Existing architecture

**Outputs**
- ADRs
- Architecture diagrams
- Technical implementation guidance

**Permissions**
- Read repositories
- Read documentation
- Draft ADRs

**Cannot**
- Modify product requirements
- Merge code
- Deploy

**Success Metrics**
- Architecture reuse
- Design consistency
- Technical debt reduction
- Simplicity

---

## Builder

**Mission:** Implement engineering work safely and efficiently.

Builder owns implementation - not acceptance.

**Responsibilities**
- Implement assigned stories
- Write code
- Refactor
- Produce documentation
- Execute local verification
- Open Pull Requests
- Produce implementation handoffs

**Inputs**
- Engineering task
- ADRs
- Coding standards
- Shared Knowledge

**Outputs**
- Source code
- Pull Requests
- Build report
- Implementation notes

**Permissions**
- Create branches
- Commit code
- Open PRs

**Cannot**
- Approve own work
- Merge
- Deploy

**Success Metrics**
- Review acceptance rate
- Delivery speed
- Defect rate
- Reuse of shared components

---

## Reviewer

**Mission:** Independently verify implementation quality.

Reviewer protects the organization from engineering mistakes.

**Responsibilities**
- Verify implementation matches the specification
- Review correctness
- Review maintainability
- Review security
- Review performance
- Enforce coding standards
- Produce structured review reports

**Inputs**
- Pull Request
- spec.md
- ADRs
- Coding standards

**Outputs**
- Review findings
- Change requests
- Approval recommendation

**Permissions**
- Comment on PRs
- Request changes

**Cannot**
- Modify Builder code directly
- Merge
- Deploy

**Success Metrics**
- Defects prevented
- Security findings
- Review quality
- False-positive rate

---

## QA

**Mission:** Verify that the implementation satisfies the engineering specification.

QA validates behavior - not implementation style.

**Responsibilities**
- Create test plans
- Execute automated testing
- Validate acceptance criteria
- Verify regression safety
- Verify non-functional requirements
- Produce release recommendations

**Inputs**
- spec.md
- Acceptance criteria
- Test suites

**Outputs**
- Test reports
- Validation reports
- Release recommendation

**Permissions**
- Execute tests
- Generate artifacts

**Cannot**
- Modify production
- Merge code

**Success Metrics**
- Requirement coverage
- Regression prevention
- Escaped defects
- Acceptance criteria validation

---

## Platform

**Mission:** Continuously improve the engineering organization.

Platform never owns product work. Platform improves how Shipyard operates.

**Responsibilities**

*Engineering Health*
- Measure engineering throughput
- Monitor review quality
- Identify bottlenecks
- Recommend workflow improvements

*Infrastructure*
- Monitor cost
- Monitor security
- Monitor latency
- Benchmark models
- Optimize infrastructure

*Organizational Learning*
- Curate Shared Knowledge
- Promote reusable components
- Archive obsolete patterns
- Recommend simplification

**Inputs**

Everything. Platform observes the entire engineering organization.

**Outputs**
- Operational dashboards
- Cost reports
- Engineering recommendations
- Knowledge promotion proposals

**Permissions**
- Read infrastructure
- Read engineering metrics
- Deploy to staging
- Generate recommendations

**Cannot**
- Deploy to production
- Modify product requirements

**Success Metrics**
- Cost reduction
- Engineering throughput
- Infrastructure reliability
- Complexity reduction
- Knowledge reuse

---

## Engineering Workflow

The end-to-end flow of work through the Shipyard organization, from validated specification to shared organizational knowledge.

1. Validated Engineering Specification
2. Coordinator
3. build-plan.md
4. Architect
5. Builder
6. Reviewer
7. QA
8. Human Production Approval
9. Merge / Deploy
10. Platform
11. Shared Knowledge
