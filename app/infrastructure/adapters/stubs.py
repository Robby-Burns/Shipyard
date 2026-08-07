import hashlib
import time
from typing import Any, Dict, Optional

from app.infrastructure.adapters.base import (
    ModelInterface,
    RepositoryInterface,
    DeploymentInterface,
)


class StubModelAdapter(ModelInterface):
    """Stub implementation of the ModelInterface for testing and local development."""

    def __init__(self, default_response: Optional[str] = None):
        self._default_response = default_response
        self._is_healthy = True

    async def check_health(self) -> bool:
        return self._is_healthy

    async def validate_config(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    async def execute_capability(
        self, capability: str, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        if self._default_response is not None:
            return self._default_response
        return f"[Stub Model response for capability '{capability}']"


class StubRepositoryAdapter(RepositoryInterface):
    """Stub implementation of the RepositoryInterface."""

    def __init__(self):
        self._is_healthy = True

    async def check_health(self) -> bool:
        return self._is_healthy

    async def validate_config(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    async def commit_code(
        self, repo_url: str, files: Dict[str, str], commit_message: str
    ) -> str:
        # Generate a deterministic mock commit hash based on files content and timestamp
        hasher = hashlib.sha1()
        hasher.update(str(files).encode("utf-8"))
        hasher.update(str(time.time()).encode("utf-8"))
        commit_hash = hasher.hexdigest()
        return commit_hash


class StubDeploymentAdapter(DeploymentInterface):
    """Stub implementation of the DeploymentInterface."""

    def __init__(self):
        self._is_healthy = True

    async def check_health(self) -> bool:
        return self._is_healthy

    async def validate_config(self) -> bool:
        return True

    async def shutdown(self) -> None:
        pass

    async def deploy(
        self, app_name: str, files: Dict[str, str], env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        sanitized_name = "".join(c if c.isalnum() else "-" for c in app_name.lower())
        return f"https://{sanitized_name}-stub-deploy.run.app"
