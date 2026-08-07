from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAdapterInterface(ABC):
    """Common interface for all infrastructure adapters."""

    @abstractmethod
    async def check_health(self) -> bool:
        """Verify connection/health of the adapter."""
        pass

    @abstractmethod
    async def validate_config(self) -> bool:
        """Validate configuration settings of the adapter."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanly release adapter resources."""
        pass


class ModelInterface(BaseAdapterInterface):
    """Interface for LLM/inference adapters."""

    @abstractmethod
    async def execute_capability(
        self, capability: str, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Send prompt to the model and return completion text."""
        pass


class RepositoryInterface(BaseAdapterInterface):
    """Interface for source control repository operations."""

    @abstractmethod
    async def commit_code(
        self, repo_url: str, files: Dict[str, str], commit_message: str
    ) -> str:
        """Commit files to a branch and return the commit hash."""
        pass


class DeploymentInterface(BaseAdapterInterface):
    """Interface for platform deployment operations (e.g. Cloud Run, Vercel)."""

    @abstractmethod
    async def deploy(
        self, app_name: str, files: Dict[str, str], env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """Deploy application artifacts and return the deployment URL."""
        pass
