from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.config.settings import settings
from app.schemas.infrastructure import InfrastructureStatusResponse, InfrastructureComponent
from app.services.auth import get_current_user
from app.infrastructure.adapters.factory import (
    get_model_adapter,
    get_repository_adapter,
    get_deployment_adapter,
)

router = APIRouter(prefix="/api/v1/infrastructure", tags=["Infrastructure"])


@router.get("", response_model=InfrastructureStatusResponse)
async def get_infrastructure_status(
    user: dict = Depends(get_current_user),
) -> InfrastructureStatusResponse:
    # 1. Models Component
    model_adapter = get_model_adapter()
    model_health = await model_adapter.check_health()
    model_details = {
        "Capabilities & Routing": {
            "Architecture Design": settings.default_model_architecture,
            "Code Generation": settings.default_model_coding,
            "Code Review Analysis": settings.default_model_code_review,
            "QA / Test Verification": settings.default_model_testing,
            "General Intake & Learning": settings.default_model_general_reasoning,
        },
        "Endpoint URL": settings.openrouter_base_url,
    }
    components = [
        InfrastructureComponent(
            name="Models",
            provider="OpenRouter" if settings.openrouter_api_key != "mock-key" else "Mock Provider",
            adapter=model_adapter.__class__.__name__,
            status="Operational" if model_health else "Degraded",
            health=model_health,
            details=model_details,
        )
    ]

    # 2. Repository Component
    repo_adapter = get_repository_adapter()
    repo_health = await repo_adapter.check_health()
    components.append(
        InfrastructureComponent(
            name="Repository",
            provider="GitHub",
            adapter=repo_adapter.__class__.__name__,
            status="Active" if repo_health else "Disconnected",
            health=repo_health,
            details={
                "Repository URL": "https://github.com/Robby-Burns/Shipyard",
                "Default Branch": "main",
                "Commit Mode": "Push Gateway",
            },
        )
    )

    # 3. Deployment Component
    dep_adapter = get_deployment_adapter()
    dep_health = await dep_adapter.check_health()
    components.append(
        InfrastructureComponent(
            name="Deployment",
            provider="Railway",
            adapter=dep_adapter.__class__.__name__,
            status="Active" if dep_health else "Inactive",
            health=dep_health,
            details={
                "Target Region": "us-east-1",
                "Deployment Domain": "https://shipyard-stub-deploy.run.app",
                "Orchestrator": "Docker Compose Engine",
            },
        )
    )

    # 4. Memory (Database) Component
    db_type = "PostgreSQL"
    if "sqlite" in settings.database_url:
        db_type = "SQLite"
    
    # Simple check: database connectivity using async engine
    from app.database.session import engine
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        db_health = True
    except Exception:
        db_health = False

    components.append(
        InfrastructureComponent(
            name="Memory",
            provider=db_type,
            adapter="SQLAlchemyDatabaseAdapter",
            status="Connected" if db_health else "Offline",
            health=db_health,
            details={
                "Database Engine": db_type,
                "Private Memory Retention": f"{settings.private_memory_retention_days} days",
                "Proposed Knowledge Retention": f"{settings.proposed_candidate_retention_days} days",
            },
        )
    )

    # 5. Storage Component
    components.append(
        InfrastructureComponent(
            name="Storage",
            provider="Amazon S3",
            adapter="StubStorageAdapter",
            status="Active",
            health=True,
            details={
                "Target Bucket": "shipyard-artifacts",
                "Permissions": "Read-Write Private Access",
                "Artifact Encryption": "AES-256 Enabled",
            },
        )
    )

    return InfrastructureStatusResponse(status="operational", components=components)
