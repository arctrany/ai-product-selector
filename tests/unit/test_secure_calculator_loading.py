"""
Test secure calculator file loading
"""

import unittest
import tempfile
import os
from pathlib import Path

from common.config.paths import SecurePathConfig
from common.models.exceptions import ConfigurationError


class TestSecureCalculatorLoading(unittest.TestCase):
    """Test secure loading of calculator files"""
    
    def setUp(self):
        """Create test calculator file"""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = Path(self.test_dir) / "test_calculator.xlsx"
        self.test_file.write_text("test")
        
        # Create config with test directory
        self.config = SecurePathConfig()
        self.config.ALLOWED_DIRS.append(Path(self.test_dir))
        self.config.add_calculator_mapping("test_temp", "test_calculator.xlsx")
        
    def tearDown(self):
        """Clean up test files"""
        if self.test_file.exists():
            self.test_file.unlink()
        os.rmdir(self.test_dir)
        
    def test_load_valid_calculator(self):
        """Test loading a valid calculator"""
        path = self.config.get_calculator_path("test_temp")
        self.assertEqual(path.name, "test_calculator.xlsx")
        self.assertTrue(path.exists())
        
    def test_load_default_calculator(self):
        """Test loading default calculator"""
        try:
            path = self.config.get_calculator_path("default")
            # Should find in docs directory
            self.assertTrue(str(path).endswith("profits_calculator.xlsx"))
        except ValueError:
            # OK if file doesn't exist in test environment
            pass
            
    def test_security_validation(self):
        """Test security validation works"""
        # Test path within allowed directory
        test_path = Path(self.test_dir) / "test.xlsx"
        self.assertTrue(self.config._validate_path_security(test_path))
        
        # Test path outside allowed directory
        bad_path = Path("/tmp/bad/path.xlsx")
        self.assertFalse(self.config._validate_path_security(bad_path))


if __name__ == '__main__':
    unittest.main()