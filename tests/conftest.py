import pytest
import os

def pytest_collection_modifyitems(items):
    """Mark all tests as forked by default."""
    for item in items:
        item.add_marker("forked")

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--workflow-config",
        action="store",
        default="tests/workflow_test_configs/test_url_sources_notes2flash_workflow_config.yml",
        help="Path to the workflow config file to test"
    )

@pytest.fixture
def workflow_config(request):
    """Get workflow config path from command line option or use default."""
    config_path = request.config.getoption("--workflow-config")
    assert os.path.exists(config_path), f"Workflow config not found at: {config_path}"
    return config_path

@pytest.fixture(params=[
    {
        "url": "https://docs.google.com/document/d/1VX_86MHD9BtyjdjAb8QZfF457H55MI_xy2M5_1zFuYw/edit?tab=t.0",
        "deckname": "Test Google Doc Deck",
        "source_type": "googledoc"
    },
    {
        "url": "https://colmsam.notion.site/Notes2Flash-Notion-Test-12e9dbe5b94080cd9810c80df7e3e221",
        "deckname": "Test Notion Deck",
        "source_type": "notion"
    },
    {
        "url": "https://obsius.site/2v1e5g2j566s7071371k",
        "deckname": "Test Obsius Deck",
        "source_type": "obsius"
    }
])
def source_config(request):
    """Fixture to provide different source configurations."""
    return request.param
