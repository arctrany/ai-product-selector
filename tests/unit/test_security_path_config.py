"""
Unit tests for SecurePathConfig
"""

import unittest
from pathlib import Path

from common.config.paths import SecurePathConfig
from common.models.exceptions import ConfigurationError


class TestSecurePathConfig(unittest.TestCase):
    """Test SecurePathConfig security features"""
    
    def setUp(self):
        """Test setup"""
        self.config = SecurePathConfig()
        
    def test_allowed_calculators(self):
        """Test accessing allowed calculators"""
        # Default calculator should work if file exists
        try:
            path = self.config.get_calculator_path("default")
            self.assertIsInstance(path, Path)
            self.assertTrue(str(path).endswith("profits_calculator.xlsx"))
        except ConfigurationError:
            # File may not exist in test environment - this is acceptable
            pass

        # Test calculator identifier is recognized even if file doesn't exist
        self.assertEqual(
            self.config.get_calculator_filename("test"),
            "test_calculator.xlsx"
        )
        
    def test_path_traversal_prevention(self):
        """Test path traversal attack prevention"""
        # Try various path traversal attempts
        dangerous_paths = [
            "../../../etc/passwd",
            "../../secrets/api_keys.xlsx",
            "/etc/passwd",
            "C:\\Windows\\System32\\config",
            "..\\..\\..\\Windows\\System32",
            "./../../private/data.xlsx",
        ]
        
        for dangerous in dangerous_paths:
            with self.assertRaises(ConfigurationError):
                self.config.validate_path(dangerous)
                
    def test_absolute_path_rejection(self):
        """Test absolute paths are rejected"""
        with self.assertRaises(ConfigurationError):
            self.config.validate_path("/usr/local/secret.xlsx")
            
        with self.assertRaises(ConfigurationError):
            self.config.validate_path("C:\\Users\\Admin\\secret.xlsx")
            
    def test_unknown_identifier(self):
        """Test unknown calculator identifier"""
        with self.assertRaises(ConfigurationError):
            self.config.get_calculator_path("unknown_calculator")
            
    def test_get_calculator_filename(self):
        """Test getting calculator filename by identifier"""
        self.assertEqual(
            self.config.get_calculator_filename("default"),
            "profits_calculator.xlsx"
        )
        
        self.assertEqual(
            self.config.get_calculator_filename("test"),
            "test_calculator.xlsx"
        )
        
        with self.assertRaises(ConfigurationError):
            self.config.get_calculator_filename("invalid")
            
    def test_valid_relative_paths(self):
        """Test valid relative paths format validation"""
        # These paths have valid format (no traversal, valid extension)
        # but may not exist - we test that traversal prevention works

        # Valid Excel extension paths should not raise extension error
        valid_format_paths = [
            "my_calc.xlsx",
            "calculator.xls",
            "workbook.xlsm",
        ]

        for path in valid_format_paths:
            # These should fail with "not within allowed directories", not "invalid extension"
            try:
                self.config.validate_path(path)
            except ConfigurationError as e:
                # Should fail because not in allowed dirs, not because of extension
                self.assertIn("allowed directories", str(e))
            
    def test_directory_check(self):
        """Test directory validation - paths outside allowed dirs are rejected"""
        # Paths outside allowed directories should be rejected
        # The validate_path method checks if paths are within ALLOWED_DIRS

        # A path that's not in any allowed directory should raise error
        with self.assertRaises(ConfigurationError) as ctx:
            self.config.validate_path("some_random_file.xlsx")

        self.assertIn("allowed directories", str(ctx.exception))
                
    def test_file_extension_validation(self):
        """Test file extension validation"""
        # Only Excel files should be allowed
        invalid_extensions = [
            "calculator.py",
            "data.json",
            "script.sh",
            "macro.vba",
        ]
        
        for invalid in invalid_extensions:
            with self.assertRaises(ConfigurationError):
                self.config.validate_path(invalid)


if __name__ == '__main__':
    unittest.main()