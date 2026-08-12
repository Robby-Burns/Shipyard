import pytest
from app.infrastructure.adapters.base import (
    ModelInterface,
    RepositoryInterface,
    DeploymentInterface,
)
from app.infrastructure.adapters.factory import (
    get_model_adapter,
    get_repository_adapter,
    get_deployment_adapter,
    reset_adapters,
)
from app.infrastructure.adapters.stubs import (
    StubModelAdapter,
    RepositoryAdapter,
    StubDeploymentAdapter,
)


@pytest.mark.anyio
async def test_stub_model_adapter():
    adapter = StubModelAdapter()
    assert isinstance(adapter, ModelInterface)
    assert await adapter.check_health() is True
    assert await adapter.validate_config() is True

    res = await adapter.execute_capability("coding", "Write a class")
    assert "Stub Model response for capability 'coding'" in res

    custom_adapter = StubModelAdapter(default_response="Custom Response")
    res_custom = await custom_adapter.execute_capability("coding", "Write a class")
    assert res_custom == "Custom Response"


@pytest.mark.anyio
async def test_repository_adapter_stub_mode():
    adapter = RepositoryAdapter()
    assert isinstance(adapter, RepositoryInterface)
    assert await adapter.check_health() is True
    assert await adapter.validate_config() is True

    files = {"main.py": "print('hello')"}
    commit_hash = await adapter.commit_code(
        "https://github.com/shipyard-ai/workflow-run", files, "feat: init"
    )
    assert isinstance(commit_hash, str)
    assert len(commit_hash) == 40


@pytest.mark.anyio
async def test_stub_deployment_adapter():
    adapter = StubDeploymentAdapter()
    assert isinstance(adapter, DeploymentInterface)
    assert await adapter.check_health() is True
    assert await adapter.validate_config() is True

    url = await adapter.deploy("My-Amazing-App", {"dist/index.html": "Hello"})
    assert url == "https://my-amazing-app-stub-deploy.run.app"


def test_adapter_factory():
    reset_adapters()
    model = get_model_adapter()
    repo = get_repository_adapter()
    deploy = get_deployment_adapter()

    assert isinstance(model, StubModelAdapter)
    assert isinstance(repo, RepositoryAdapter)
    assert isinstance(deploy, StubDeploymentAdapter)

    # Verify singleton behavior
    assert get_model_adapter() is model
    assert get_repository_adapter() is repo
    assert get_deployment_adapter() is deploy
