import pytest
import os
import hashlib
import time
from unittest.mock import patch, MagicMock
from app.infrastructure.adapters.stubs import RepositoryAdapter
from app.infrastructure.adapters.base import RepositoryInterface


@pytest.mark.anyio
async def test_repository_adapter_scheme_validation():
    adapter = RepositoryAdapter()
    
    # Test valid scheme
    assert isinstance(adapter, RepositoryInterface)
    
    # Test invalid schemes
    with pytest.raises(ValueError, match="secure https:// scheme"):
        await adapter.commit_code("http://github.com/org/repo.git", {}, "feat: commit")
        
    with pytest.raises(ValueError, match="secure https:// scheme"):
        await adapter.commit_code("ssh://git@github.com/org/repo.git", {}, "feat: commit")

    with pytest.raises(ValueError, match="secure https:// scheme"):
        await adapter.commit_code("file:///etc/passwd", {}, "feat: commit")


@pytest.mark.anyio
async def test_repository_adapter_requires_token_for_user_repository():
    adapter = RepositoryAdapter()
    
    # A user repository must fail loudly instead of silently returning a fake
    # commit hash when the server has not been configured with a token.
    with patch.dict(os.environ, {"GIT_TOKEN": ""}):
        with pytest.raises(RuntimeError, match="GIT_TOKEN"):
            await adapter.commit_code(
                "https://github.com/org/repo.git", {"a.py": "1"}, "test commit"
            )
        
    # The internal placeholder remains an explicit local/test stub.
    with patch.dict(os.environ, {"GIT_TOKEN": "some_token"}):
        commit_hash = await adapter.commit_code("https://github.com/shipyard-ai/workflow-run", {"a.py": "1"}, "test commit")
        assert len(commit_hash) == 40  # Returns mock hash


@pytest.mark.anyio
async def test_repository_adapter_push_success():
    adapter = RepositoryAdapter()
    files = {"src/main.py": "print('ok')"}
    token = "secret_github_token_value_abc"
    repo_url = "https://github.com/test-org/test-repo.git"
    
    # Mock subprocess.run to simulate git commands
    mock_run = MagicMock()
    # Configure mock responses for clone, config, add, commit, push, rev-parse
    mock_responses = [
        MagicMock(returncode=0, stdout="Cloned successfully"), # git clone
        MagicMock(returncode=0), # git config user.name
        MagicMock(returncode=0), # git config user.email
        MagicMock(returncode=0), # git add src/main.py
        MagicMock(returncode=0, stdout="[main a1b2c3d] test commit\n1 file changed\n"), # git commit
        MagicMock(returncode=0, stdout="Pushed successfully"), # git push
        MagicMock(returncode=0, stdout="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2\n") # git rev-parse
    ]
    mock_run.side_effect = mock_responses
    
    with patch.dict(os.environ, {"GIT_TOKEN": token}):
        with patch("subprocess.run", mock_run):
            commit_hash = await adapter.commit_code(repo_url, files, "test commit")
            
            assert commit_hash == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
            
            # Verify the subprocesses were executed
            assert mock_run.call_count == 7
            
            # Verify git clone was called with the username injected
            clone_args = mock_run.call_args_list[0][0][0]
            assert clone_args[0] == "git"
            assert clone_args[1] == "clone"
            assert clone_args[2] == "https://oauth2@github.com/test-org/test-repo.git"
            
            # Verify scoped git add of only specific file
            add_args = mock_run.call_args_list[3][0][0]
            assert add_args[0] == "git"
            assert add_args[1] == "add"
            assert add_args[2] == os.path.normpath("src/main.py")


@pytest.mark.anyio
async def test_repository_adapter_push_fail_and_censorship():
    adapter = RepositoryAdapter()
    files = {"src/main.py": "print('ok')"}
    token = "super_secret_github_token_value_xyz"
    repo_url = "https://github.com/test-org/test-repo.git"
    
    # Simulate a git clone failure that prints the token in stderr
    mock_run = MagicMock()
    mock_run.return_value = MagicMock(
        returncode=128,
        stderr=f"fatal: Authentication failed for 'https://{token}@github.com/test-org/test-repo.git'"
    )
    
    with patch.dict(os.environ, {"GIT_TOKEN": token}):
        with patch("subprocess.run", mock_run):
            with pytest.raises(RuntimeError) as exc_info:
                await adapter.commit_code(repo_url, files, "test commit")
                
            # Verify git failed and threw an exception
            assert "Git clone failed" in str(exc_info.value)
            # Verify the token is censored and was never leaked
            assert token not in str(exc_info.value)
            assert "*****" in str(exc_info.value)
