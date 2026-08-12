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
class RepositoryAdapter(RepositoryInterface):
    """Dual-mode RepositoryInterface implementation supporting Git cloning/pushing and mock stub hashes."""

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
        import os
        import tempfile
        import subprocess
        import shutil
        import sys
        from app.config.settings import settings
        import structlog
        
        logger = structlog.get_logger("repository_adapter")
        
        token = os.environ.get("GIT_TOKEN") or settings.git_token
        
        # 1. Scheme Validation
        if repo_url:
            if not repo_url.startswith("https://"):
                raise ValueError("Security violation: Repository URL must use the secure https:// scheme.")

        # 2. Execution Branching
        # The workflow-run repository remains an explicit local/test stub.
        # A user-provided repository must never silently become a fake commit
        # just because Railway is missing its server-side GitHub token.
        is_mock = "github.com/shipyard-ai/workflow-run" in (repo_url or "")
        if not is_mock and not token:
            raise RuntimeError(
                "GitHub push is not configured. Add GIT_TOKEN to the server environment."
            )
        
        if is_mock:
            # Mock Stub Commit Hash Generation
            hasher = hashlib.sha1()
            hasher.update(str(files).encode("utf-8"))
            hasher.update(str(time.time()).encode("utf-8"))
            return hasher.hexdigest()

        # 3. Real Git Commit & Push (Fail-Loud)
        temp_dir = tempfile.mkdtemp()
        askpass_path = None
        try:
            # Create a secure askpass script within the temp directory
            askpass_ext = ".bat" if os.name == "nt" else ".sh"
            askpass_path = os.path.join(temp_dir, f"askpass_{hash(time.time())}{askpass_ext}")
            
            # Setup owner-only file permissions (0600 on POSIX)
            if os.name != "nt":
                # Create file with 0600 permissions
                fd = os.open(askpass_path, os.O_WRONLY | os.O_CREAT, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(f'#!/bin/sh\necho "{token}"\n')
                os.chmod(askpass_path, 0o700) # Execute permission for owner
            else:
                with open(askpass_path, "w", encoding="utf-8") as f:
                    f.write(f"@echo {token}\n")

            env = {
                **os.environ,
                "GIT_ASKPASS": askpass_path,
                "GIT_TERMINAL_PROMPT": "0",
            }

            # Map auth username based on repository domain
            auth_username = "oauth2"
            if "bitbucket.org" in repo_url:
                auth_username = "x-token-auth"
            
            auth_url = repo_url.replace("https://", f"https://{auth_username}@")

            # Clone repository
            logger.info("Cloning remote git repository", repo_url=repo_url)
            clone_res = subprocess.run(
                ["git", "clone", auth_url, temp_dir],
                env=env,
                capture_output=True,
                text=True,
            )
            if clone_res.returncode != 0:
                # Sanitise error message to prevent token leak
                err_msg = clone_res.stderr.replace(token, "*****")
                raise RuntimeError(f"Git clone failed: {err_msg}")

            # Write generated files
            logger.info("Writing build files to cloned repository", files=list(files.keys()))
            for file_path, file_content in files.items():
                # Prevent directory traversal vulnerability checks
                clean_path = os.path.normpath(file_path)
                if clean_path.startswith("..") or os.path.isabs(clean_path):
                    raise ValueError(f"Security violation: Invalid file path {file_path}")
                
                full_path = os.path.join(temp_dir, clean_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

            # Config local git user
            subprocess.run(["git", "config", "user.name", "Shipyard AI"], cwd=temp_dir, env=env, check=True)
            subprocess.run(["git", "config", "user.email", "bot@shipyard.ai"], cwd=temp_dir, env=env, check=True)

            # Scoped git add of only the specific generated file paths
            logger.info("Staging and committing files to branch")
            for file_path in files.keys():
                clean_path = os.path.normpath(file_path)
                add_res = subprocess.run(
                    ["git", "add", clean_path],
                    cwd=temp_dir,
                    env=env,
                    capture_output=True,
                    text=True,
                )
                if add_res.returncode != 0:
                    err_msg = add_res.stderr.replace(token, "*****")
                    raise RuntimeError(f"Git add failed for {file_path}: {err_msg}")

            # Commit changes
            commit_res = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            if commit_res.returncode != 0:
                # If nothing changed, we can ignore or log it. Let's make sure we log and proceed
                if "nothing to commit" in commit_res.stdout or "no changes added to commit" in commit_res.stdout:
                    logger.info("Nothing to commit (files are unchanged)")
                else:
                    err_msg = commit_res.stderr.replace(token, "*****")
                    raise RuntimeError(f"Git commit failed: {err_msg}")

            # Push to origin
            logger.info("Pushing changes to remote git repository")
            push_res = subprocess.run(
                ["git", "push", "origin", "HEAD"],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            if push_res.returncode != 0:
                err_msg = push_res.stderr.replace(token, "*****")
                raise RuntimeError(f"Git push failed: {err_msg}")

            # Retrieve commit hash
            rev_res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=temp_dir,
                env=env,
                capture_output=True,
                text=True,
            )
            if rev_res.returncode != 0:
                err_msg = rev_res.stderr.replace(token, "*****")
                raise RuntimeError(f"Git rev-parse failed: {err_msg}")
            
            commit_hash = rev_res.stdout.strip()
            # Double check hash does not contain token
            if token in commit_hash:
                raise RuntimeError("Security breach: Commit hash contained token.")
            return commit_hash

        except Exception as e:
            # Sanitise any exception message to guarantee token is never leaked
            sanitised_err = str(e).replace(token, "*****") if token else str(e)
            logger.error("Git integration error during push", error=sanitised_err)
            raise RuntimeError(sanitised_err) from None

        finally:
            # Strict cleanup in finally block
            try:
                if askpass_path and os.path.exists(askpass_path):
                    os.remove(askpass_path)
            except Exception:
                pass
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass


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
