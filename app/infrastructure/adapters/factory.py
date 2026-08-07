from typing import Dict, Any
from app.infrastructure.adapters.base import (
    ModelInterface,
    RepositoryInterface,
    DeploymentInterface,
)
from app.infrastructure.adapters.stubs import (
    StubModelAdapter,
    StubRepositoryAdapter,
    StubDeploymentAdapter,
)

# Registry to keep singletons/instances if needed
_adapters: Dict[str, Any] = {}


def get_model_adapter() -> ModelInterface:
    """Get the active model adapter (defaults to stub for local dev)."""
    if "model" not in _adapters:
        _adapters["model"] = StubModelAdapter()
    return _adapters["model"]


def get_repository_adapter() -> RepositoryInterface:
    """Get the active repository adapter (defaults to stub for local dev)."""
    if "repository" not in _adapters:
        _adapters["repository"] = StubRepositoryAdapter()
    return _adapters["repository"]


def get_deployment_adapter() -> DeploymentInterface:
    """Get the active deployment adapter (defaults to stub for local dev)."""
    if "deployment" not in _adapters:
        _adapters["deployment"] = StubDeploymentAdapter()
    return _adapters["deployment"]


def reset_adapters() -> None:
    """Clear cached adapter instances (primarily for testing)."""
    _adapters.clear()
