import sys
import os
from pathlib import Path
import pytest

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the addon module
from addon.notes2flash import notes2flash

class TestNotes2Flash:
    """Test notes2flash functionality with different config files"""

    @pytest.fixture
    def base_user_inputs(self):
        """Base user inputs that can be extended per test"""
        return {}

    def test_notes2flash_with_config(self, config_path, base_user_inputs):
        """
        Test notes2flash with a specific config file
        
        Args:
            config_path: Path to the workflow config file to test
            base_user_inputs: Fixture providing base user inputs
        """
        try:
            result = notes2flash(
                workflow_config_path=config_path,
                user_inputs=base_user_inputs,
                debug=True
            )
            assert isinstance(result, dict), "Expected result to be a dictionary"
        except Exception as e:
            pytest.fail(f"notes2flash failed with config {config_path}: {str(e)}")

    def test_invalid_inputs(self, config_path):
        """Test error handling with invalid inputs"""
        # Test empty config path
        with pytest.raises(ValueError):
            notes2flash(
                workflow_config_path="",
                user_inputs={}
            )

        # Test None user inputs
        with pytest.raises(ValueError):
            notes2flash(
                workflow_config_path=config_path,
                user_inputs=None
            )

        # Test non-existent config path
        with pytest.raises(Exception):
            notes2flash(
                workflow_config_path="non_existent_config.yml",
                user_inputs={}
            )

if __name__ == '__main__':
    pytest.main([__file__])
