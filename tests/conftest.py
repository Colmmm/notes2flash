import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--config-path",
        action="store",
        default="addon/workflow_configs/googledoc_github_actions_test_config.yml",
        help="Path to the workflow config file to test"
    )

@pytest.fixture
def config_path(request):
    return request.config.getoption("--config-path")
