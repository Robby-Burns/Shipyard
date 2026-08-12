# Shipyard Implementation Guide

> This is a normalized reference roadmap. It describes phased target capabilities and design intent, not the authoritative current implementation status. Current runtime behavior is governed by `../foundation/current_implementation_alignment.md`.

## Phase 1 - Foundation

### Goal

Establish a simple, reliable engineering foundation that every future capability depends on.

Phase 1 intentionally contains no AI orchestration, engineering disciplines, or autonomous behavior.

The objective is to create a stable platform that is easy to understand, easy to deploy, and easy to maintain.

**Principle: Keep it boring.**

### Objectives

Build a production-ready application skeleton that provides:
- API framework
- Configuration management
- Database connectivity
- Authentication
- Logging
- Error handling
- Deployment pipeline
- Basic monitoring

At the completion of this phase, Shipyard should deploy successfully, expose a healthy API, persist data, and support future expansion without architectural changes.

### Deliverables

**Application**
- FastAPI application
- Standard project structure
- Environment configuration
- Dependency management
- Health endpoints

**Infrastructure**
- Docker
- Docker Compose
- Railway deployment
- PostgreSQL (or Supabase)
- GitHub repository
- GitHub Actions

**Core Services**
- Structured logging
- Configuration service
- Database service
- Secrets management
- Error handling
- Basic metrics

**Security**
- Environment-based secrets
- Authentication middleware
- Role-based configuration
- Secure defaults

### Acceptance Criteria

Phase 1 is complete when:
- The application deploys automatically.
- Health endpoints respond successfully.
- Configuration loads from environment variables.
- Database migrations execute successfully.
- Logs are structured and searchable.
- CI/CD completes successfully.
- Secrets never exist in source control.
- Local development requires minimal setup.

### Directory Structure

```
shipyard/
+-- app/
+-- api/
+-- config/
+-- database/
+-- services/
+-- infrastructure/
+-- tests/
+-- scripts/
+-- docker/
`-- docs/
```

Keep the directory structure intentionally small. Avoid creating folders for future ideas.

### Design Principles

During this phase:
- Prefer simple solutions over clever ones.
- Build only what is immediately required.
- Keep dependencies minimal.
- Favor readability over abstraction.
- Avoid premature optimization.

Every component added during Phase 1 should have a clear purpose.

### Human Responsibilities

Humans remain responsible for:
- Technology selection
- Infrastructure decisions
- Security review
- Deployment approval
- Repository governance

Shipyard provides no autonomous engineering capabilities during this phase.

### Not Included

Do not build:
- Workflow Engine
- Engineering disciplines
- Model Router
- Tool Gateway
- Memory system
- Shared Knowledge
- Autonomous workflows
- AI agents
- Vector databases
- Multi-model orchestration
- Knowledge promotion
- Release automation beyond CI/CD

These capabilities belong to later phases.

### Exit Criteria

Before beginning Phase 2:
- [x] The application deploys reliably.
- [x] Infrastructure is reproducible.
- [x] CI/CD is operational.
- [x] Logging and monitoring function correctly.
- [x] Security fundamentals are in place.
- [x] Developers can clone the repository and begin working in minutes.

### Why This Phase Exists

Every future capability depends on a stable foundation.

Adding AI before establishing reliable infrastructure creates unnecessary complexity and makes debugging significantly harder.

Phase 1 intentionally delays intelligence in favor of stability.

A simple, well-tested foundation reduces the cost of every future phase.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Phase 2 - Core Platform Services

### Goal

Build the foundational platform services that enable the Shipyard engineering organization.

These services provide the infrastructure required for secure tool execution, model abstraction, operational logging, and future workflow orchestration.

No engineering discipline is implemented during this phase.

**Principle: Build the platform before building the organization.**

### Objectives

Create the shared platform services that every engineering discipline will use.

These services become the stable interfaces between Shipyard and external systems.

At the completion of this phase, Shipyard should be capable of securely executing tools, routing AI requests, recording operational history, and exposing common platform services.

### Deliverables

**Model Router**

Provide a single interface for AI model access.

Responsibilities include:
- Model abstraction
- Capability-based routing
- Provider failover
- Cost tracking
- Model configuration
- Organizational routing policies

Engineering disciplines request capabilities - not specific models. Examples include:
- Architecture reasoning
- Software implementation
- Code review
- Testing
- General analysis

The Model Router determines which model satisfies each request.

**Tool Gateway**

Provide secure access to external systems.

Responsibilities include:
- Authentication
- Authorization
- Tool execution
- Response validation
- Error handling
- Activity logging

The Tool Gateway becomes the only component permitted to access infrastructure. Examples include:
- GitHub
- Railway
- Docker
- OpenRouter
- RunPod
- Supabase
- Slack
- Email

Engineering disciplines never receive infrastructure credentials.

**Memory Gateway**

Provide a single interface for organizational memory.

Responsibilities include:
- Read memory
- Write memory
- Search memory
- Context retrieval
- Version management

Memory implementation is intentionally minimal during this phase. Knowledge lifecycle is implemented in Phase 3.

**Activity Log**

Maintain a complete operational history.

Responsibilities include:
- Workflow events
- Tool execution
- Model requests
- Errors
- Performance metrics
- Audit history

Every infrastructure action should be recorded. Operational history supports debugging, observability, and organizational improvement.

### Platform Interfaces

Every core service should expose a stable API. Examples include:

```
Model Router
  route(capability, context)

Tool Gateway
  execute(tool, action, payload)

Memory Gateway
  retrieve(query)
  store(record)

Activity Log
  record(event)
  search(filters)
```

Implementation details may evolve without changing these interfaces.

### Design Principles

During this phase:
- Build stable interfaces before implementations.
- Prefer composition over tight coupling.
- Hide infrastructure complexity behind services.
- Minimize direct dependencies.
- Keep APIs simple and deterministic.

Every service should have a single responsibility.

### Human Responsibilities

Humans remain responsible for:
- Model provider selection
- Infrastructure configuration
- Security policies
- Integration approval
- External service credentials

Shipyard executes through these services but never owns these decisions.

### Not Included

Do not build:
- Workflow Engine
- Coordinator
- Architect
- Builder
- Reviewer
- QA
- Shared Knowledge
- Knowledge promotion
- Human approval workflow
- Engineering dashboards
- Autonomous planning

Those capabilities belong to later phases.

### Exit Criteria

Before beginning Phase 3:
- [x] Model Router successfully routes requests by capability.
- [x] Tool Gateway securely executes infrastructure operations.
- [x] Memory Gateway provides basic storage and retrieval.
- [x] Activity Log records all platform operations.
- [x] External services are isolated behind platform interfaces.
- [x] Engineering disciplines can be implemented without modifying platform services.

### Why This Phase Exists

The engineering organization should never depend directly on external tools or AI providers.

By introducing the Model Router, Tool Gateway, Memory Gateway, and Activity Log before any engineering disciplines, Shipyard creates a stable platform that can evolve independently of models, providers, or infrastructure.

This separation ensures that future improvements - such as adopting a new AI model, changing deployment platforms, or expanding integrations - require changes only within the platform services rather than throughout the engineering organization.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Phase 3 - Organizational Memory

### Goal

Establish the organizational memory system that allows Shipyard to learn, reuse knowledge, and improve over time.

The objective is to create durable engineering knowledge while preventing temporary context from becoming permanent organizational memory.

**Principle: Experience compounds. Context expires.**

### Objectives

Build the memory architecture that supports every engineering discipline.

At the completion of this phase, Shipyard should distinguish between temporary working memory, candidate knowledge, permanent organizational knowledge, and external reference material.

Knowledge should become a managed engineering asset rather than accumulated conversation history.

### Memory Architecture

Shipyard maintains four categories of memory.

**Private Memory**

Private Memory belongs to an individual engineering discipline. Examples include:
- Current task context
- Temporary reasoning
- Active implementation notes
- Working decisions
- Session history

Private Memory is temporary. It expires when no longer useful. It is never promoted automatically.

**Candidate Knowledge**

Candidate Knowledge contains information that may benefit the organization but has not yet been approved. Examples include:
- New architecture patterns
- Useful implementation techniques
- Security observations
- Performance improvements
- Reusable utilities
- Documentation improvements

Candidate Knowledge is reviewed before becoming permanent.

**Shared Knowledge**

Shared Knowledge represents curated organizational memory. Examples include:
- Architecture Decision Records
- Coding Standards
- Reusable Components
- Testing Strategies
- Security Practices
- Deployment Procedures
- Operational Playbooks

Shared Knowledge supports every engineering discipline. Only humans approve promotion into Shared Knowledge.

**External Knowledge**

External Knowledge contains reference material outside Shipyard. Examples include:
- Framework documentation
- API documentation
- Product documentation
- Industry standards
- Research papers

External Knowledge remains external. It is never copied into Shared Knowledge without review.

### Knowledge Lifecycle

Knowledge progresses through defined stages.

```
Private Memory
  |
  v
Candidate Knowledge
  |
  Human Review
  |
  v
Shared Knowledge
```

Temporary context should expire. Permanent knowledge should be intentionally curated.

### Memory Gateway Integration

The Memory Gateway introduced in Phase 2 now supports:
- Context retrieval
- Semantic search
- Knowledge storage
- Knowledge versioning
- Memory expiration
- Access control

Engineering disciplines access memory only through the Memory Gateway. They never access storage directly.

### Knowledge Principles

During this phase:
- Store knowledge, not conversations.
- Promote patterns, not one-off solutions.
- Prefer reusable guidance over implementation details.
- Keep Shared Knowledge intentionally small.
- Archive obsolete knowledge.

Every permanent addition should improve future engineering work.

### Human Responsibilities

Humans remain responsible for:
- Approving Shared Knowledge
- Removing obsolete knowledge
- Resolving conflicting guidance
- Reviewing organizational standards
- Governing long-term memory

Shipyard may recommend knowledge promotion. Only humans approve it.

### Not Included

Do not build:
- Workflow Engine
- Engineering disciplines
- Autonomous planning
- Engineering dashboards
- Product discovery
- Customer memory
- Business strategy memory
- Automatic knowledge promotion
- Self-modifying memory

Those capabilities belong to later phases.

### Exit Criteria

Before beginning Phase 4:
- [x] Memory Gateway supports retrieval and storage.
- [x] Private Memory is isolated.
- [x] Candidate Knowledge is operational.
- [x] Shared Knowledge is searchable.
- [x] Knowledge versioning functions correctly.
- [x] Human approval governs knowledge promotion.
- [x] Temporary memory expires appropriately.

### Design Principles

Organizational memory should:
- Improve engineering quality
- Reduce repeated mistakes
- Increase consistency
- Preserve institutional knowledge
- Remain understandable

Knowledge quality is more important than knowledge quantity.

### Why This Phase Exists

Every engineering organization accumulates experience.

Without a structured memory system, that experience disappears when projects end or conversations are forgotten.

By separating Private Memory, Candidate Knowledge, Shared Knowledge, and External Knowledge, Shipyard ensures that only proven, reusable engineering knowledge becomes part of the organization's long-term memory.

This distinction prevents knowledge bloat, keeps organizational guidance trustworthy, and allows Shipyard to continuously improve without becoming increasingly complex.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Phase 4 - Engineering Organization

### Goal

Implement the Shipyard engineering organization by introducing the engineering disciplines and the workflow that coordinates them.

At the completion of this phase, Shipyard can accept an Approved Engineering Specification, execute engineering work through independent disciplines, and produce a release candidate ready for human approval.

**Principle: Separate responsibilities. Verify independently.**

### Objectives

Build the engineering workflow that transforms an approved engineering specification into production-ready software.

Each discipline has a single responsibility. No discipline verifies its own work. No discipline owns product strategy.

### Engineering Workflow

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
```

Engineering work always moves forward through independent verification.

### Workflow Engine

**Purpose**

Coordinate engineering work without performing engineering work.

The Workflow Engine manages progression through the engineering lifecycle.

**Responsibilities**
- Start workflows
- Route work between disciplines
- Maintain workflow state
- Pause for human approval
- Handle escalation
- Record workflow history
- Resume execution

The Workflow Engine never modifies engineering artifacts.

### Engineering Disciplines

Shipyard consists of six engineering disciplines.

**Coordinator** - Owns engineering workflow.

Responsibilities include:
- Creating engineering tasks
- Coordinating implementation
- Managing workflow progress
- Escalating ambiguity
- Coordinating releases

The Coordinator owns workflow - not engineering decisions.

**Architect** - Owns implementation architecture.

Responsibilities include:
- Reviewing the engineering specification
- Producing implementation guidance
- Creating Architecture Decision Records
- Defining interfaces
- Identifying technical risk

The Architect never changes product intent.

**Builder** - Owns implementation.

Responsibilities include:
- Writing code
- Refactoring
- Documentation
- Unit testing
- Pull Requests

Builder never approves its own work.

**Reviewer** - Owns independent engineering verification.

Responsibilities include:
- Code review
- Security review
- Performance review
- Maintainability review
- Standards enforcement

Reviewer evaluates implementation. Reviewer does not rewrite requirements.

**QA** - Owns specification validation.

Responsibilities include:
- Acceptance testing
- Regression testing
- Integration validation
- Release recommendation

QA validates behavior - not implementation style.

**Platform** - Owns organizational improvement.

Responsibilities include:
- Engineering metrics
- Operational health
- Cost monitoring
- Model evaluation
- Complexity analysis
- Knowledge recommendations

Platform observes the organization. Platform does not deliver features.

### Model Router Integration

Every engineering discipline requests capabilities rather than specific AI models. Examples include:

```
Builder    -> Best Coding Capability
Reviewer   -> Best Review Capability
QA         -> Best Testing Capability
```

The Model Router determines which model satisfies each capability request. Disciplines remain model-agnostic.

### Human Decision Gates

Shipyard pauses execution whenever human judgment is required.

Required approvals include:
- Ambiguous specifications
- Conflicting requirements
- High-risk implementation plans
- Architecture changes affecting product intent
- Production deployment

Shipyard never changes requirements without human approval.

### Risk-Based Workflow

Every engineering task receives a declared risk level.

- LOW
- MEDIUM
- HIGH

Risk determines:
- Review depth
- Testing depth
- Human approvals
- Deployment requirements

Engineering rigor scales with implementation risk.

### Independent Verification

Shipyard intentionally separates implementation from verification.

```
Builder
  v
Reviewer
  v
QA
```

Whenever practical:
- Builder and Reviewer should use different AI model families.
- QA should validate work independently of Builder.
- No discipline approves its own work.

Independent verification improves reliability and reduces systemic bias.

### Platform Integration

Platform observes every engineering workflow. Examples include:
- Workflow duration
- Review quality
- Defect rates
- Cost
- Latency
- Model performance
- Knowledge reuse

Platform recommends improvements. Humans decide whether to adopt them.

### Not Included

Do not build:
- Product discovery
- Customer interviews
- Roadmap planning
- Feature prioritization
- Business decisions
- Autonomous deployment
- Automatic knowledge promotion

Those responsibilities belong outside Shipyard.

### Exit Criteria

Before beginning Phase 5:
- [x] Workflow Engine coordinates engineering execution.
- [x] Every discipline performs its assigned responsibility.
- [x] Model Router supports capability-based routing.
- [x] Independent verification is operational.
- [x] Human approval gates function correctly.
- [x] Release candidates are consistently produced.
- [x] Platform observes engineering workflows.

### Design Principles

During this phase:
- One responsibility per discipline.
- Independent verification over self-correction.
- Human approval for irreversible decisions.
- Stable workflows over clever automation.
- Simplicity over feature count.

Every discipline should remain understandable and replaceable.

### Why This Phase Exists

This phase transforms Shipyard from a collection of platform services into an AI-native engineering organization.

By separating coordination, architecture, implementation, review, validation, and organizational improvement into distinct disciplines, Shipyard mirrors the strengths of high-performing engineering teams while remaining model-agnostic.

The engineering disciplines do not compete - they collaborate through a structured workflow, with independent verification and human oversight ensuring that engineering decisions remain reliable, auditable, and aligned with the approved engineering specification.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Phase 5 - Platform Operations

### Goal

Implement the Platform discipline that continuously measures, evaluates, and improves the Shipyard engineering organization.

Platform does not participate in feature delivery. Platform improves how Shipyard operates.

**Principle: Measure before optimizing.**

### Objectives

Build the operational capabilities required to monitor engineering performance, identify improvement opportunities, and support organizational learning.

At the completion of this phase, Shipyard should understand how well it operates without changing engineering workflows autonomously.

Platform observes. Humans decide.

### Responsibilities

Platform continuously evaluates the health of the engineering organization. Areas of responsibility include:
- Engineering throughput
- Workflow efficiency
- Operational reliability
- Infrastructure utilization
- Model performance
- Knowledge reuse
- Complexity management
- Cost optimization

Platform never owns feature implementation.

### Operational Metrics

Platform collects engineering metrics including:

**Workflow**
- Cycle time
- Review duration
- Testing duration
- Release frequency
- Human approval time

**Quality**
- Review findings
- QA failures
- Regression defects
- Escaped defects
- Requirement coverage

**Infrastructure**
- Tool Gateway latency
- Model Router latency
- Infrastructure availability
- Service reliability

**Models**
- Cost
- Response time
- Success rate
- Failure rate
- Routing effectiveness

Model selection remains the responsibility of the Model Router. Platform measures outcomes rather than selecting models directly.

**Knowledge**
- Knowledge reuse
- Candidate promotions
- Obsolete knowledge
- Search effectiveness

### Recommendations

Platform generates recommendations such as:
- Simplify workflows
- Improve routing policies
- Retire unused components
- Reduce infrastructure costs
- Promote reusable patterns
- Archive obsolete knowledge

Recommendations never execute automatically. Humans approve organizational changes.

### Organizational Health

Platform continuously evaluates:
- Engineering velocity
- Operational stability
- Workflow bottlenecks
- Complexity growth
- Knowledge quality

The objective is continuous improvement rather than feature delivery.

### Dashboards

Platform provides operational visibility into:
- Active projects
- Workflow status
- Engineering metrics
- Infrastructure health
- Cost trends
- Model utilization
- Knowledge growth

Dashboards support decision making. They never replace human judgment.

### Human Responsibilities

Humans remain responsible for:
- Accepting recommendations
- Organizational policy
- Budget decisions
- Performance targets
- Infrastructure strategy
- Process changes

Platform provides evidence. Humans make decisions.

### Not Included

Do not build:
- Automatic workflow changes
- Autonomous process optimization
- Automatic model replacement
- Autonomous deployments
- Automatic knowledge promotion
- Product analytics
- Customer analytics
- Business intelligence

Those responsibilities belong outside Platform.

### Exit Criteria

Before beginning Phase 6:
- [x] Engineering metrics are collected.
- [x] Operational dashboards function correctly.
- [x] Platform generates actionable recommendations.
- [x] Organizational health can be evaluated objectively.
- [x] Human approval governs organizational improvements.
- [x] No Platform recommendation executes automatically.

### Design Principles

During this phase:
- Measure before optimizing.
- Prefer evidence over intuition.
- Recommend rather than automate.
- Reduce complexity whenever possible.
- Improve the organization - not individual features.

Platform exists to make Shipyard better over time.

### Why This Phase Exists

Engineering organizations naturally accumulate complexity as they grow.

Without objective measurement, bottlenecks remain hidden, infrastructure costs increase, and engineering practices slowly diverge.

Platform provides continuous visibility into how Shipyard operates, allowing humans to make informed decisions based on evidence rather than intuition.

By separating observation from execution, Platform improves organizational performance without compromising human governance or introducing unnecessary automation.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Phase 6 - Operations Console

### Goal

Build the primary human interface for interacting with the Shipyard engineering organization.

The Operations Console provides visibility, approvals, and operational control without participating in engineering execution.

**Principle: Humans direct. Shipyard executes.**

### Objectives

Provide a single interface where humans can:
- Submit approved engineering specifications
- Monitor engineering workflows
- Review release candidates
- Approve production deployments
- Review organizational recommendations
- Manage Shared Knowledge

The Operations Console is an interface - not an engineering discipline.

### Core Capabilities

**Project Management**

Support:
- Create projects
- View project status
- Monitor workflow progress
- Review engineering history
- Archive completed work

The console reflects the current state of Shipyard. It does not replace the Workflow Engine.

**Workflow Visibility**

Provide visibility into:
- Current engineering discipline
- Active task
- Workflow history
- Escalations
- Human approvals
- Release readiness

Humans should always understand where engineering work is.

**Release Management**

Support:
- Review Release Candidates
- Review test results
- Review code review summaries
- Review architecture decisions
- Approve production deployment

Production deployment always requires human approval.

**Platform Visibility**

Display:
- Engineering metrics
- Operational health
- Cost
- Infrastructure status
- Model utilization
- Recommendations

Platform recommendations remain advisory.

**Knowledge Management**

Provide access to:
- Shared Knowledge
- Candidate Knowledge
- Architecture Decisions
- Coding Standards
- Operational Playbooks

Knowledge promotion remains human controlled.

### Human Responsibilities

Humans use the Operations Console to:
- Submit approved engineering specifications
- Resolve escalations
- Review release candidates
- Approve deployments
- Promote Shared Knowledge
- Accept organizational recommendations

The Operations Console supports decision making. It never replaces human judgment.

### Design Principles

The Operations Console should be:
- Simple
- Fast
- Readable
- Auditable
- Explainable

Every screen should answer a single question. Avoid dashboards that require training to understand.

### Not Included

Do not build:
- AI chat interfaces
- Autonomous decision making
- Product management features
- Customer management
- Business analytics
- Prompt editing
- Workflow editing

Those responsibilities belong elsewhere.

### Exit Criteria

Before completing Phase 6:
- [x] Projects can be monitored.
- [x] Engineering workflows are visible.
- [x] Release candidates can be reviewed.
- [x] Human approvals function correctly.
- [x] Platform recommendations are accessible.
- [x] Shared Knowledge can be reviewed and managed.
- [x] Every engineering decision is traceable.

### Why This Phase Exists

Shipyard is designed to augment engineering teams - not replace them.

The Operations Console provides a clear, auditable interface between humans and the engineering organization.

Rather than requiring users to inspect logs, databases, or infrastructure directly, the console presents the current state of engineering work in a way that supports informed decision making while preserving human authority over strategic and irreversible decisions.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Advanced Capability A - Organizational Maturity (Optional)

### Goal

Extend Shipyard through continuous organizational improvement rather than additional engineering complexity.

Shipyard is fully operational after Phase 6.

Advanced Capability A focuses on refining the engineering organization through evidence, measurement, and experience.

**Principle: Improve what exists before adding something new.**

### Objectives

Continuously improve the effectiveness of the engineering organization by refining existing capabilities.

Areas of focus include:
- Engineering workflow
- Model routing
- Shared Knowledge
- Operational efficiency
- Infrastructure utilization
- Engineering quality

No new engineering disciplines are introduced during this capability.

### Areas of Improvement

**Workflow Optimization**

Evaluate opportunities to:
- Reduce engineering cycle time
- Remove unnecessary workflow steps
- Improve human approvals
- Simplify coordination

Every workflow improvement should reduce complexity.

**Model Routing Optimization**

Continuously improve routing policies through operational evidence. Examples include:
- Better capability matching
- Lower operational cost
- Improved fallback strategies
- Reduced latency

Engineering disciplines remain model-agnostic.

**Knowledge Quality**

Continuously improve:
- Shared Knowledge
- Candidate Knowledge
- Documentation quality
- Search relevance
- Knowledge reuse

Retire obsolete knowledge regularly.

**Platform Optimization**

Evaluate opportunities to:
- Reduce infrastructure costs
- Improve reliability
- Remove unnecessary services
- Improve observability
- Simplify platform architecture

Platform should become simpler over time.

**Engineering Standards**

Continuously evaluate:
- Coding Standards
- Architecture Decision Records
- Testing Practices
- Deployment Procedures
- Security Guidance

Standards evolve through operational evidence rather than opinion.

### Human Responsibilities

Humans remain responsible for:
- Organizational policy
- Process improvements
- Technology strategy
- Knowledge promotion
- Workflow approval

Shipyard recommends improvements. Humans approve organizational change.

### Not Included

Do not build:
- New engineering disciplines
- Autonomous engineering management
- Autonomous product strategy
- Autonomous budgeting
- Autonomous organizational restructuring

Shipyard improves engineering. Humans lead engineering.

### Exit Criteria

Advanced Capability A is an ongoing capability rather than a project. Success is demonstrated through:
- [x] Reduced operational complexity
- [x] Improved engineering quality
- [x] Greater knowledge reuse
- [x] Lower infrastructure costs
- [x] Faster engineering throughput
- [x] Stable human governance

### Design Principles

During this capability:
- Simplify before expanding.
- Remove before adding.
- Measure before optimizing.
- Prefer operational excellence over new functionality.
- Keep the organization understandable.

Every improvement should make Shipyard easier to operate.

### Why This Capability Exists

Engineering organizations improve through disciplined refinement rather than continuous expansion.

Once Shipyard reaches operational maturity, the greatest gains come from simplifying workflows, strengthening organizational knowledge, improving engineering practices, and reducing unnecessary complexity.

Advanced Capability A ensures that Shipyard evolves through measured improvement while remaining aligned with its core principles of simplicity, independent verification, and human governance.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.

---

## Advanced Capability B - Engineering Intelligence (Optional)

### Goal

Enable Shipyard to proactively identify engineering risks, recommend improvements, and provide decision support without assuming ownership of engineering decisions.

Engineering Intelligence augments the engineering organization. It never replaces engineering judgment.

**Principle: Inform decisions. Never make them.**

### Objectives

Analyze engineering activity across projects to surface patterns that improve engineering quality and organizational effectiveness. Examples include:
- Technical debt identification
- Architecture consistency
- Reusable component discovery
- Risk prediction
- Engineering trend analysis
- Delivery forecasting

Engineering Intelligence recommends. Humans decide.

### Capabilities

**Engineering Insights**

Continuously identify:
- Technical debt
- Repeated implementation patterns
- Duplicate components
- Workflow bottlenecks
- Review quality trends

Surface findings as recommendations.

**Architecture Intelligence**

Evaluate engineering projects for:
- Architecture consistency
- Reuse opportunities
- Interface stability
- Dependency growth
- Complexity trends

Recommend improvements before complexity accumulates.

**Risk Intelligence**

Analyze engineering work for indicators such as:
- Large implementation scope
- High review churn
- Repeated QA failures
- Increasing complexity
- Security concerns

Risk assessments support - not replace - engineering judgment.

**Knowledge Intelligence**

Identify opportunities to:
- Promote reusable knowledge
- Archive obsolete guidance
- Improve documentation
- Merge duplicate patterns
- Improve search quality

Knowledge promotion always requires human approval.

**Delivery Intelligence**

Provide operational forecasts including:
- Estimated completion
- Workflow bottlenecks
- Infrastructure utilization
- Cost trends
- Engineering throughput

Forecasts are advisory.

### Human Responsibilities

Humans remain responsible for:
- Engineering decisions
- Organizational priorities
- Risk acceptance
- Technology direction
- Process improvements

Engineering Intelligence provides evidence. Humans determine action.

### Design Principles

Engineering Intelligence should:
- Explain every recommendation.
- Provide supporting evidence.
- Avoid unnecessary complexity.
- Prefer simple recommendations.
- Remain transparent.

Recommendations should always be understandable.

### Not Included

Do not build:
- Autonomous planning
- Autonomous architecture changes
- Automatic workflow modifications
- Automatic deployments
- Automatic knowledge promotion
- Product strategy
- Customer analytics
- Business forecasting

Engineering Intelligence supports engineering. It never manages engineering.

### Success Criteria

Engineering Intelligence demonstrates value through:
- [x] Earlier risk identification
- [x] Better architectural consistency
- [x] Reduced technical debt
- [x] Improved knowledge reuse
- [x] More predictable delivery
- [x] Better engineering decisions

### Why This Capability Exists

As Shipyard matures, operational data becomes increasingly valuable.

Rather than simply collecting metrics, Engineering Intelligence analyzes engineering activity to identify patterns that humans might otherwise overlook.

This capability enables Shipyard to improve continuously through evidence while preserving the organization's commitment to human leadership and intentional decision making.

Engineering Intelligence does not automate engineering management. It strengthens it.

**Stop Here.** Before beginning the next Phase, verify what you have built. Double check that all exit criteria has been built and is operational.
