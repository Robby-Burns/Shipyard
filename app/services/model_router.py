from typing import Any, Dict, Optional

from fastapi import HTTPException
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.config.settings import settings
from app.schemas.model_router import (
    Capability,
    ModelRouteRequest,
    ModelRouteResponse,
)
from app.services.activity_log import ActivityLogService

logger = structlog.get_logger()


class ModelRouterService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.activity_log_service = ActivityLogService(db)

    def resolve_model(self, capability: Capability) -> str:
        capability_map = {
            Capability.ARCHITECTURE: settings.default_model_architecture,
            Capability.CODING: settings.default_model_coding,
            Capability.CODE_REVIEW: settings.default_model_code_review,
            Capability.TESTING: settings.default_model_testing,
            Capability.GENERAL_REASONING: settings.default_model_general_reasoning,
            Capability.CHALLENGE: settings.default_model_challenge,
        }
        return capability_map.get(
            capability, settings.default_model_general_reasoning
        )

    async def route(
        self, request: ModelRouteRequest, request_id: Optional[str] = None
    ) -> ModelRouteResponse:
        model_name = self.resolve_model(request.capability)
        if request.metadata and "model_override" in request.metadata:
            model_name = request.metadata["model_override"]


        # Log routing attempt
        await self.activity_log_service.record(
            event_type="model_route_started",
            source="model_router",
            request_id=request_id,
            payload={"capability": request.capability.value, "model": model_name},
        )

        # Mock fallback for development/testing if API key is mock
        if settings.openrouter_api_key == "mock-key":
            response = ModelRouteResponse(
                id="mock-completion-id",
                capability=request.capability,
                model_used=model_name,
                content=self._get_mock_content(request),
                usage={
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30,
                },
            )
        else:
            headers = {
                "Authorization": f"Bearer {settings.openrouter_api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model_name,
                "messages": [msg.model_dump() for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

            # Normalize the configured URL so either the API root or the full
            # completion endpoint can be supplied without creating a bad path.
            configured_url = settings.openrouter_base_url.rstrip("/")
            completion_url = (
                configured_url
                if configured_url.endswith("/chat/completions")
                else f"{configured_url}/chat/completions"
            )
            upstream_error_code = None
            upstream_error_message = None

            try:
                async with httpx.AsyncClient() as client:
                    res = await client.post(
                        completion_url,
                        json=payload,
                        headers=headers,
                        timeout=30.0,
                    )

                    # Preserve the provider's actionable error before
                    # raise_for_status() turns it into a generic exception.
                    if res.is_error:
                        try:
                            upstream_payload = res.json()
                        except ValueError:
                            upstream_payload = None

                        if isinstance(upstream_payload, dict):
                            upstream_error = upstream_payload.get(
                                "error", upstream_payload
                            )
                            if isinstance(upstream_error, dict):
                                upstream_error_code = upstream_error.get("code")
                                upstream_error_message = upstream_error.get("message")
                            else:
                                upstream_error_message = str(upstream_error)
                        else:
                            upstream_error_message = res.text[:500].strip() or None

                    res.raise_for_status()
                    data = res.json()

                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})

                    response = ModelRouteResponse(
                        id=data.get("id", "completion-id"),
                        capability=request.capability,
                        model_used=model_name,
                        content=content,
                        usage=usage,
                    )
            except httpx.TimeoutException as exc:
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=504,
                    detail="Gateway Timeout – OpenRouter API request timed out",
                )
            except (httpx.ConnectError, httpx.NetworkError) as exc:
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=503,
                    detail="Service Unavailable – failed to connect to OpenRouter API",
                )
            except httpx.HTTPStatusError as exc:
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "endpoint": completion_url,
                        "upstream_status": exc.response.status_code,
                        "upstream_code": upstream_error_code,
                        "upstream_message": upstream_error_message,
                        "error": str(exc),
                    },
                )
                if upstream_error_message:
                    raise HTTPException(
                        status_code=502,
                        detail=(
                            "Bad Gateway - OpenRouter rejected the request "
                            f"with status code {exc.response.status_code}: "
                            f"{upstream_error_message}"
                        ),
                    )
                raise HTTPException(
                    status_code=502,
                    detail=f"Bad Gateway – OpenRouter API returned status code {exc.response.status_code}",
                )
            except Exception as exc:
                await self.activity_log_service.record(
                    event_type="model_route_failed",
                    source="model_router",
                    request_id=request_id,
                    payload={
                        "capability": request.capability.value,
                        "model": model_name,
                        "error": str(exc),
                    },
                )
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal Server Error – failed to process Model Router response: {str(exc)}",
                )

        # Record completion log
        await self.activity_log_service.record(
            event_type="model_route_completed",
            source="model_router",
            request_id=request_id,
            payload={
                "capability": request.capability.value,
                "model": model_name,
                "usage": response.usage,
            },
        )

        return response

    def _get_mock_content(self, request: ModelRouteRequest) -> str:
        # Determine caller by scanning messages
        system_prompt = ""
        user_prompt = ""
        for msg in request.messages:
            if msg.role == "system":
                system_prompt = msg.content
            elif msg.role == "user":
                user_prompt = msg.content

        # 0. Challenger/Verifier Agent
        if "Challenger/Verifier" in system_prompt or "verifier" in system_prompt.lower() or "challenger" in system_prompt.lower():
            if "intentionally_fail" in user_prompt or "mock_challenge_fail" in user_prompt:
                return '<challenge status="failed" reason="Intentionally failed challenge verification check for testing."></challenge>'
            return '<challenge status="passed"></challenge>'

        # 1. Intake Coordinator / Specification Writer
        if "Intake Coordinator" in system_prompt or "Specification Writer" in system_prompt:
            last_user_msg = ""
            for msg in reversed(request.messages):
                if msg.role == "user":
                    last_user_msg = msg.content
                    break
            
            user_msgs = [m for m in request.messages if m.role == "user"]
            
            # Extract title if any
            project_title = "Operational Performance Monitor"
            for msg in user_msgs:
                content_lower = msg.content.lower()
                if "payment" in content_lower or "stripe" in content_lower:
                    project_title = "Payment Integration Service"
                    break
                elif "auth" in content_lower or "login" in content_lower or "permission" in content_lower:
                    project_title = "Role-Based Authentication Module"
                    break
                elif "dashboard" in content_lower or "analytics" in content_lower or "portal" in content_lower:
                    project_title = "Analytics Portal Upgrade"
                    break

            is_validating = False
            if "Specification Writer" in system_prompt:
                is_validating = True
            elif last_user_msg:
                msg_clean = last_user_msg.lower().strip()
                if any(kw in msg_clean for kw in ["validate", "yes", "confirm", "proceed", "approve", "go ahead", "start"]):
                    is_validating = True
                elif len(last_user_msg) > 150:
                    is_validating = True
            
            if is_validating:
                return "VALIDATED\n" + self._generate_mock_specification(project_title)
            else:
                return (
                    "I am the Engineering Intake Coordinator. I've analyzed your project idea. [Mock Response]\n\n"
                    "To generate a validated Engineering Specification, please provide or confirm details for:\n"
                    "- **Overview & Background**: Project scope and target users.\n"
                    "- **Functional Requirements**: Core capabilities and endpoints.\n"
                    "- **Non-Functional Requirements**: Security and latency expectations.\n"
                    "- **Technical Architecture Constraints**: Programming language and database stack.\n"
                    "- **Deployment & Infrastructure Constraints**: Port configuration and deployment target.\n\n"
                    "*(Tip: You can type 'validate' or 'yes' to generate the engineering specification immediately!)*"
                )

        # 2. Coordinator (Build plan or Passport Compilation)
        elif "Coordinator for the Shipyard" in system_prompt:
            if "engineering_passport" in user_prompt or "Engineering Passport" in user_prompt:
                return self._compile_engineering_passport(user_prompt)
            else:
                project_title = "Operational Performance Monitor"
                if "Payment" in user_prompt or "payment" in user_prompt:
                    project_title = "Payment Integration Service"
                elif "Auth" in user_prompt or "auth" in user_prompt:
                    project_title = "Role-Based Authentication Module"
                return self._generate_mock_build_plan(project_title)

        # 3. Architect
        elif "Architect for the Shipyard" in system_prompt:
            project_title = "Operational Performance Monitor"
            if "Payment" in user_prompt or "payment" in user_prompt:
                project_title = "Payment Integration Service"
            elif "Auth" in user_prompt or "auth" in user_prompt:
                project_title = "Role-Based Authentication Module"
            return self._generate_mock_architecture(project_title)

        # 4. Builder
        elif "Builder for the Shipyard" in system_prompt:
            project_title = "Operational Performance Monitor"
            if "Payment" in user_prompt or "payment" in user_prompt:
                project_title = "Payment Integration Service"
            elif "Auth" in user_prompt or "auth" in user_prompt:
                project_title = "Role-Based Authentication Module"
            return self._generate_mock_builder_code(project_title)

        # 5. Reviewer
        elif "Reviewer for the Shipyard" in system_prompt:
            return self._generate_mock_reviewer_feedback()

        # 6. QA
        elif "QA Engineer" in system_prompt:
            return self._generate_mock_qa_feedback()

        # 7. Platform
        elif "Platform Engineer" in system_prompt:
            return self._generate_mock_platform_feedback()

        # Fallback default
        return f"[Mock Response for {request.capability.value} using {self.resolve_model(request.capability)}]"

    def _generate_mock_specification(self, project_title: str) -> str:
        return f"""# Engineering Specification: {project_title}

## 1. Overview & Background
The objective of this project is to implement a high-performance **{project_title}** system that integrates into the existing Shipyard platform architecture. The target audience includes core system developers and downstream client applications requiring unified interface endpoints.

## 2. Functional Requirements
- **FR-001**: Implement structured JSON payload intake with schemas checks.
- **FR-002**: Generate detailed activity trails and log them to the Engineering Journal.
- **FR-003**: Provide a clean dashboard view mapping active adapter status, health checks, and connection protocols.
- **FR-004**: Expose standardized health (`/healthz`) and readiness (`/readyz`) endpoints.

## 3. Non-Functional Requirements
- **NFR-001 (Performance)**: Average API response latency must be less than 150ms under concurrent workloads.
- **NFR-002 (Security)**: Enforce JSON Web Token (JWT) verification for all endpoints under the `/api/v1/` prefix.
- **NFR-003 (Robustness)**: Gracefully handle network disconnects, logging failures, and adapter exceptions without leaking system internals.

## 4. Technical Architecture Constraints
- **Language**: Python 3.11+
- **Framework**: FastAPI (using asynchronous routers and handlers)
- **Database**: PostgreSQL (SQLAlchemy 2.0 with asyncpg driver)
- **Logging**: Structlog structured logging output

## 5. Deployment & Infrastructure Constraints
- **Environment**: Containerized Docker image (`shipyard-app:latest`)
- **Port Mapping**: Expose port `8000` inside the container
- **Deployment Host**: Deployed via Railway cloud orchestrator
- **Environment Variables**:
  - `DATABASE_URL` (Connection string)
  - `JWT_SECRET_KEY` (Auth signature)
  - `APP_ENV` (development/production)
"""

    def _generate_mock_build_plan(self, project_title: str) -> str:
        return f"""# Engineering Build Plan: {project_title}

This plan details the phases for building {project_title}.

## Phase 1: Core Service Setup
- Initialize classes in `app/core/service.py`
- Setup validation logic and exception raising

## Phase 2: Integration & DB
- Bind database interface configurations
- Configure asynchronous session context managers

## Phase 3: Validation Testing
- Implement async unit tests in `tests/test_service.py`
- Validate performance and boundaries
"""

    def _generate_mock_architecture(self, project_title: str) -> str:
        return f"""# Architectural Design for {project_title}

We have designed a modular, interface-driven layout to implement the {project_title} requirements.

<diagram>
```mermaid
graph TD
    Client[Web Frontend / Client API] -->|HTTPS / JWT| Gateway[FastAPI API Gateway]
    Gateway -->|Async Middleware| MainApp[Core Application Logic]
    MainApp -->|Adapter Interface| DB[(PostgreSQL Database)]
    MainApp -->|Adapter Interface| Cache[(Redis Cache)]
    MainApp -->|Adapter Interface| Storage[S3 Object Store]
```
</diagram>

<adr id="ADR-001">
# ADR-001: Asynchronous Database Choice

## Context
The system needs to persist project records, activity journals, and adapter logs. The data must remain relational and indexable.

## Decision
We choose PostgreSQL as the database provider, interacting through SQLAlchemy 2.0 async session pools.

## Rationale
Ensures ACID transactions and horizontal scaling. Swappable behind the Database Interface to SQLite for tests.
</adr>

<adr id="ADR-002">
# ADR-002: Adapter Registry Pattern for Replaceable Infrastructure

## Context
We need to swap between mock stubs and real providers for third-party services like models, repositories, and deployments.

## Decision
We enforce the Adapter registry pattern where concrete providers (GitHub, Railway, Claude, Gemini) implement the base interface.

## Rationale
No technology choice is hardcoded. It protects the core workflow systems from vendor lock-in.
</adr>
"""

    def _generate_mock_builder_code(self, project_title: str) -> str:
        return """# Builder Implementation Code

I have built the source files and test suites following the architecture constraints.

<file path="app/core/service.py">
import structlog
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class CoreEngineeringService:
    \"\"\"Handles core execution workflow validation and event logging.\"\"\"
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.active = True

    async def process_task(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("processing_task_started", task_id=task_id)
        if not payload:
            raise ValueError("Empty execution payload")
        
        result = {
            "status": "success",
            "task_id": task_id,
            "processed_at": "2026-08-10T10:54:00Z",
            "output": f"Processed payload of size {len(payload)}"
        }
        logger.info("processing_task_completed", task_id=task_id, result=result)
        return result
</file>

<file path="tests/test_service.py">
import pytest
from app.core.service import CoreEngineeringService

@pytest.mark.anyio
async def test_process_task_success():
    service = CoreEngineeringService({"env": "testing"})
    res = await service.process_task("test-123", {"action": "build"})
    assert res["status"] == "success"
    assert res["task_id"] == "test-123"

@pytest.mark.anyio
async def test_process_task_validation_error():
    service = CoreEngineeringService({"env": "testing"})
    with pytest.raises(ValueError):
        await service.process_task("test-123", {})
</file>

<test_results>
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
rootdir: c:\\Users\\burns\\OneDrive\\Documents\\GitHub\\Shipyard
plugins: anyio-4.2.0, cov-4.1.0
collected 2 items

tests/test_service.py ..                                                 [100%]

============================== 2 passed in 0.08s ===============================
</test_results>
"""

    def _generate_mock_reviewer_feedback(self) -> str:
        return """# Code Review Analysis

I have completed the review of the builder's code changes.

## Findings
- **Architecture Compliant**: Code resides in `app/core/service.py` under clean service abstractions.
- **Vulnerabilities**: Input payload keys are verified. No direct string interpolation in SQL queries.
- **Testing**: Tests include async setup and verify both happy paths and exception paths.

<review status="approved"></review>
"""

    def _generate_mock_qa_feedback(self) -> str:
        return """# QA Verification Report

We ran automated functional and regression validation checks.

## Metrics
- **Unit Tests**: 2/2 Passed
- **Code Coverage**: 100.0%
- **Latency SLA Check**: Passed (Average response 42ms)
- **Accessibility Check**: Passed (100% compliant)

<qa_status>PASSED</qa_status>
"""

    def _generate_mock_platform_feedback(self) -> str:
        return """# Platform Recommendations

Pipeline operations metrics have been collected and processed.

<recommendations>
- Configure PostgreSQL connection pool `max_overflow` limit to 10 for peak usage periods.
- Enforce structlog JSON output formatting in non-development environments.
</recommendations>

<knowledge_candidate>
### Asynchronous Database Pools in FastAPI

When defining database adapters with SQLAlchemy, ensure the engine is created globally and disposal is registered on the FastAPI shutdown hook. This prevents orphaned open connection streams on redeployments.
</knowledge_candidate>
"""

    def _compile_engineering_passport(self, user_prompt: str) -> str:
        import os
        import re
        
        # Extract files from prompt context
        files_match = re.search(r"['\"]files['\"]: \[(.*?)\]", user_prompt)
        if files_match:
            files_list = [f.strip(" '\"") for f in files_match.group(1).split(",")]
        else:
            files_list = ["app/core/service.py", "tests/test_service.py"]
            
        # Extract commit hash
        commit_match = re.search(r"['\"]commit_hash['\"]: ['\"](.*?)['\"]", user_prompt)
        commit_hash = commit_match.group(1) if commit_match else "7a8f9c1d2e3f0b"
        
        # Extract title
        title_match = re.search(r"['\"]title['\"]: ['\"](.*?)['\"]", user_prompt)
        project_title = title_match.group(1) if title_match else "Operational Performance Monitor"
        
        files_str = "\n".join(f"- `{f}`" for f in files_list)
        
        repo_tour = (
            "The repository is organized following clean architecture boundaries:\n"
            f"- `app/core/`: Contains the core service implementations. Specifically, `app/core/service.py` contains the business logic for task processing.\n"
            f"- `tests/`: Contains isolated test suites. `tests/test_service.py` validates processing outcomes and bounds checking.\n"
            "- `app/infrastructure/`: Hosts technology-specific adapters (database, storage, repository gateways)."
        )

        explain_project = (
            "### 👔 For Executives\n"
            "This project modernizes our core execution pipeline, shifting to async database pooling. This decreases infrastructure overhead by 40% and ensures stable operations during transaction spikes.\n\n"
            "### 📋 For Product Managers\n"
            "The changes support higher API throughput, enabling the product to scale to thousands of active concurrent sessions without lag or degradation.\n\n"
            "### 🛠️ For Engineering Managers\n"
            "We've established clean adapter boundaries. If we decide to swap S3 for Google Cloud Storage or move databases, developers can do so in a single config change without touching core logic.\n\n"
            "### 💻 For Developers\n"
            "You can run the service locally by initializing `CoreEngineeringService(config)`. Tests are written using pytest and are fully async.\n\n"
            "### 🔒 For Security Teams\n"
            "No credentials are hardcoded. Input boundaries are strictly checked and exceptions are cleanly handled to prevent stack trace leaks.\n\n"
            "### 👥 For Customers\n"
            "Ensures transactions are processed instantly and reliably, backed by a robust backend architecture."
        )

        timeline = (
            f"- **Intake Completed**: Engineering Specification approved and finalized.\n"
            f"- **Architecture Verified**: Component diagrams and ADRs designed.\n"
            f"- **Build Completed**: Code committed under branch hash `{commit_hash[:8]}`.\n"
            f"- **Review Signed-off**: Security checks and code standards verified.\n"
            f"- **QA Validated**: Async and unit verification suites passed."
        )

        passport = f"""# Engineering Passport — {project_title}

## Executive Summary
This document serves as the official release and blueprint dossier for the **{project_title}** project. It outlines the architectural patterns, files built, quality verification, and handoff instructions.

## What Was Built
The engineering team implemented the core files corresponding to the specification:
{files_str}

## Architecture & Repository Tour
### Request Flow & Diagram
```mermaid
graph TD
    Client[Web Frontend / Client API] -->|HTTPS / JWT| Gateway[FastAPI API Gateway]
    Gateway --> CoreAPI[Core Service Node]
    CoreAPI --> DB[(PostgreSQL Database)]
```

### Repository Tour
{repo_tour}

## Technology Stack
- **Backend Language**: Python 3.11+
- **Web Framework**: FastAPI (Async routes)
- **Database Connection**: SQLAlchemy 2.0 Async (asyncpg)
- **Logging**: Structlog JSON logging
- **Testing Framework**: Pytest with Asyncio

## Engineering Decisions
The Architect established the following design records:
- **ADR-001**: Asynchronous PostgreSQL Database with pgvector
- **ADR-002**: Adapter Pattern for Replaceable Infrastructure

## AI Engineering Summary
- **Coordinator**: Directed execution phases, compiled build plan, and compiled this passport.
- **Architect**: Modeled systems, drew Mermaid schemas, and wrote Architecture Decision Records.
- **Builder**: Programmed python classes, compiled test files, and pushed to the repository.
- **Reviewer**: Evaluated code quality, performance impacts, and security vulnerabilities.
- **QA**: Verified compliance with functional specs and validated readiness.
- **Platform**: Gathers logs, monitored SLAs, and formulated learning recommendations.

## Deployment Guide
### Release Blueprint
- **Release Tag**: `rel_{commit_hash[:8]}`
- **Commit Hash**: `{commit_hash}`

### Execution Steps
1. **Source Code**: Pull branch matching the commit `{commit_hash[:8]}`.
2. **Configuration**: Set up env parameters in `.env` (ports, credentials).
3. **Database Setup**: Execute migration upgrades: `alembic upgrade head`.
4. **Run Containers**: Startup the application services `docker compose up -d`.
5. **Verification**: Run diagnostic validation checks: `/healthz` and `/readyz`.

## External Dependencies & Risks
- **PostgreSQL Database**: Port 5432 must be open.
- **Security Access**: JWT secret token must be configured in environment variables.

## Explain This Project
{explain_project}

## Engineering Timeline
{timeline}
"""
        return passport
