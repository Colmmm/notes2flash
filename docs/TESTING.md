# Testing notes2flash

## Overview

The notes2flash add-on uses pytest-anki for end-to-end testing in an Anki environment. Tests verify the workflow with multiple note sources (Google Docs, Notion, Obsius) using configurable workflow configurations.

## Required Secrets

Set up these GitHub secrets:
- `OPENROUTER_API_KEY`: For model access
- `NOTION_API_KEY`: For Notion integration

## Test Configuration

The tests use a workflow config that accepts URL and deck name as user inputs. By default, it uses `tests/workflow_test_configs/test_url_sources_notes2flash_workflow_config.yml`, but you can specify a different config using the `--workflow-config` option.

The default config is tested with multiple sources:
1. Google Docs: https://docs.google.com/document/d/1VX_86MHD9BtyjdjAb8QZfF457H55MI_xy2M5_1zFuYw/edit?tab=t.0
2. Notion: https://colmsam.notion.site/Notes2Flash-Notion-Test-12e9dbe5b94080cd9810c80df7e3e221
3. Obsius: https://obsius.site/2v1e5g2j566s7071371k

## Local Testing

1. Install dependencies:
```bash
# System dependencies
sudo apt-get install xvfb qt6-base-dev

# Python dependencies
pip install pytest pytest-xvfb pytest-forked
pip install anki==23.12.1 aqt==23.12.1
pip install pytest-anki
pip install -r requirements.txt
```

2. Configure API keys in addon/config.json:
```json
{
    "openrouter_api_key": "your-key",
    "notion_api_key": "your-key"
}
```

3. Run tests:
```bash
# Run with default workflow config
pytest tests/ -v --forked

# Or specify a different workflow config
pytest tests/ -v --forked --workflow-config=path/to/your/config.yml
```

## Test Structure

- conftest.py: 
  - Common fixtures
  - Source configuration parameters
  - Workflow config handling
- test_notes2flash.py:
  - Add-on loading
  - Config validation
  - API configuration
  - Workflow execution with different sources

## Test Cases

The workflow is tested with each source to verify:
1. Content extraction from the source
2. Processing into flashcards
3. Adding cards to Anki with correct fields
4. Deck creation and management

Each test runs in isolation using pytest-anki's AnkiSession and the @pytest.mark.forked decorator.

## Adding New Tests

To test with a different workflow config:

1. Create your workflow config YAML file
2. Run tests with your config:
```bash
pytest tests/ -v --forked --workflow-config=path/to/your/config.yml
```

The tests will use your config while still testing with all configured sources.
