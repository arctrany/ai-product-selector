"""
Unit tests for ConfigManager and EnvironmentManager implementations.

Tests the configuration management functionality including:
- Multiple configuration formats support
- Configuration scopes and hierarchies
- Environment variable management
- Configuration validation and transformation
- Hot reload and file watching
"""

import unittest
import tempfile
import os
import json
import yaml
import configparser
from unittest.mock import Mock, patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src_new.rpa.browser.implementations.config_manager import (
    ConfigManager,
    EnvironmentManager
)
from src_new.rpa.browser.core import (
    IConfigManager,
    IEnvironmentManager,
    ConfigFormat,
    ConfigScope,
    ConfigurationError,
    ValidationError
)


class TestConfigManager(unittest.TestCase):
    """Test ConfigManager implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = ConfigManager()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample configuration data
        self.sample_config = {
            'database': {
                'host': 'localhost',
                'port': 5432,
                'name': 'testdb'
            },
            'api': {
                'timeout': 30,
                'retries': 3
            },
            'features': {
                'debug': True,
                'logging': 'INFO'
            }
        }
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_implements_interface(self):
        """Test that ConfigManager implements IConfigManager."""
        self.assertIsInstance(self.config_manager, IConfigManager)
    
    def test_load_json_config(self):
        """Test loading JSON configuration."""
        # Create JSON config file
        json_file = os.path.join(self.temp_dir, 'config.json')
        with open(json_file, 'w') as f:
            json.dump(self.sample_config, f)
        
        self.config_manager.load_config(json_file, ConfigFormat.JSON)
        
        # Verify configuration loaded correctly
        self.assertEqual(
            self.config_manager.get('database.host'),
            'localhost'
        )
        self.assertEqual(
            self.config_manager.get('database.port'),
            5432
        )
        self.assertTrue(
            self.config_manager.get('features.debug')
        )
    
    def test_load_yaml_config(self):
        """Test loading YAML configuration."""
        # Create YAML config file
        yaml_file = os.path.join(self.temp_dir, 'config.yaml')
        with open(yaml_file, 'w') as f:
            yaml.dump(self.sample_config, f)
        
        self.config_manager.load_config(yaml_file, ConfigFormat.YAML)
        
        # Verify configuration loaded correctly
        self.assertEqual(
            self.config_manager.get('api.timeout'),
            30
        )
        self.assertEqual(
            self.config_manager.get('api.retries'),
            3
        )
    
    def test_load_toml_config(self):
        """Test loading TOML configuration."""
        # Create TOML config file
        toml_file = os.path.join(self.temp_dir, 'config.toml')
        toml_content = """
[database]
host = "localhost"
port = 5432
name = "testdb"

[api]
timeout = 30
retries = 3

[features]
debug = true
logging = "INFO"
"""
        with open(toml_file, 'w') as f:
            f.write(toml_content)
        
        self.config_manager.load_config(toml_file, ConfigFormat.TOML)
        
        # Verify configuration loaded correctly
        self.assertEqual(
            self.config_manager.get('database.name'),
            'testdb'
        )
        self.assertEqual(
            self.config_manager.get('features.logging'),
            'INFO'
        )
    
    def test_load_ini_config(self):
        """Test loading INI configuration."""
        # Create INI config file
        ini_file = os.path.join(self.temp_dir, 'config.ini')
        config = configparser.ConfigParser()
        config['database'] = {
            'host': 'localhost',
            'port': '5432',
            'name': 'testdb'
        }
        config['api'] = {
            'timeout': '30',
            'retries': '3'
        }
        
        with open(ini_file, 'w') as f:
            config.write(f)
        
        self.config_manager.load_config(ini_file, ConfigFormat.INI)
        
        # Verify configuration loaded correctly (INI values are strings)
        self.assertEqual(
            self.config_manager.get('database.host'),
            'localhost'
        )
        self.assertEqual(
            self.config_manager.get('database.port'),
            '5432'
        )
    
    def test_load_env_config(self):
        """Test loading environment configuration."""
        # Create .env file
        env_file = os.path.join(self.temp_dir, '.env')
        env_content = """
DATABASE_HOST=localhost
DATABASE_PORT=5432
API_TIMEOUT=30
FEATURES_DEBUG=true
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        self.config_manager.load_config(env_file, ConfigFormat.ENV)
        
        # Verify configuration loaded correctly
        self.assertEqual(
            self.config_manager.get('DATABASE_HOST'),
            'localhost'
        )
        self.assertEqual(
            self.config_manager.get('DATABASE_PORT'),
            '5432'
        )
        self.assertEqual(
            self.config_manager.get('FEATURES_DEBUG'),
            'true'
        )
    
    def test_auto_detect_format(self):
        """Test automatic format detection."""
        # Create JSON file without specifying format
        json_file = os.path.join(self.temp_dir, 'auto.json')
        with open(json_file, 'w') as f:
            json.dump(self.sample_config, f)
        
        self.config_manager.load_config(json_file)  # No format specified
        
        # Should auto-detect as JSON and load correctly
        self.assertEqual(
            self.config_manager.get('database.host'),
            'localhost'
        )
    
    def test_config_scopes(self):
        """Test configuration scopes."""
        # Load global config
        global_config = {'global_setting': 'global_value'}
        json_file = os.path.join(self.temp_dir, 'global.json')
        with open(json_file, 'w') as f:
            json.dump(global_config, f)
        
        self.config_manager.load_config(json_file, scope=ConfigScope.GLOBAL)
        
        # Load module config
        module_config = {'module_setting': 'module_value'}
        json_file = os.path.join(self.temp_dir, 'module.json')
        with open(json_file, 'w') as f:
            json.dump(module_config, f)
        
        self.config_manager.load_config(json_file, scope=ConfigScope.MODULE)
        
        # Verify both configs are accessible
        self.assertEqual(
            self.config_manager.get('global_setting', scope=ConfigScope.GLOBAL),
            'global_value'
        )
        self.assertEqual(
            self.config_manager.get('module_setting', scope=ConfigScope.MODULE),
            'module_value'
        )
    
    def test_config_hierarchy(self):
        """Test configuration hierarchy and overrides."""
        # Load base config
        base_config = {
            'setting1': 'base_value1',
            'setting2': 'base_value2'
        }
        base_file = os.path.join(self.temp_dir, 'base.json')
        with open(base_file, 'w') as f:
            json.dump(base_config, f)
        
        self.config_manager.load_config(base_file, scope=ConfigScope.GLOBAL)
        
        # Load override config
        override_config = {
            'setting1': 'override_value1',  # Override
            'setting3': 'new_value3'        # New setting
        }
        override_file = os.path.join(self.temp_dir, 'override.json')
        with open(override_file, 'w') as f:
            json.dump(override_config, f)
        
        self.config_manager.load_config(override_file, scope=ConfigScope.SESSION)
        
        # Verify hierarchy: SESSION > GLOBAL
        self.assertEqual(
            self.config_manager.get('setting1'),  # Should get override value
            'override_value1'
        )
        self.assertEqual(
            self.config_manager.get('setting2'),  # Should get base value
            'base_value2'
        )
        self.assertEqual(
            self.config_manager.get('setting3'),  # Should get new value
            'new_value3'
        )
    
    def test_set_and_get_config(self):
        """Test setting and getting configuration values."""
        # Set simple value
        self.config_manager.set('simple_key', 'simple_value')
        self.assertEqual(
            self.config_manager.get('simple_key'),
            'simple_value'
        )
        
        # Set nested value
        self.config_manager.set('nested.key', 'nested_value')
        self.assertEqual(
            self.config_manager.get('nested.key'),
            'nested_value'
        )
        
        # Set with specific scope
        self.config_manager.set('scoped_key', 'scoped_value', scope=ConfigScope.MODULE)
        self.assertEqual(
            self.config_manager.get('scoped_key', scope=ConfigScope.MODULE),
            'scoped_value'
        )
    
    def test_get_with_default(self):
        """Test getting configuration with default values."""
        # Non-existent key should return default
        self.assertEqual(
            self.config_manager.get('nonexistent', default='default_value'),
            'default_value'
        )
        
        # Existing key should return actual value
        self.config_manager.set('existing_key', 'actual_value')
        self.assertEqual(
            self.config_manager.get('existing_key', default='default_value'),
            'actual_value'
        )
    
    def test_has_config(self):
        """Test checking if configuration exists."""
        # Non-existent key
        self.assertFalse(self.config_manager.has('nonexistent'))
        
        # Set and check existing key
        self.config_manager.set('existing_key', 'value')
        self.assertTrue(self.config_manager.has('existing_key'))
        
        # Check nested key
        self.config_manager.set('nested.key', 'value')
        self.assertTrue(self.config_manager.has('nested.key'))
    
    def test_delete_config(self):
        """Test deleting configuration values."""
        # Set and verify key exists
        self.config_manager.set('to_delete', 'value')
        self.assertTrue(self.config_manager.has('to_delete'))
        
        # Delete and verify key is gone
        self.config_manager.delete('to_delete')
        self.assertFalse(self.config_manager.has('to_delete'))
        
        # Delete nested key
        self.config_manager.set('nested.to_delete', 'value')
        self.assertTrue(self.config_manager.has('nested.to_delete'))
        
        self.config_manager.delete('nested.to_delete')
        self.assertFalse(self.config_manager.has('nested.to_delete'))
    
    def test_get_all_config(self):
        """Test getting all configuration."""
        # Set some values
        self.config_manager.set('key1', 'value1')
        self.config_manager.set('key2', 'value2')
        self.config_manager.set('nested.key', 'nested_value')
        
        all_config = self.config_manager.get_all()
        
        self.assertIn('key1', all_config)
        self.assertIn('key2', all_config)
        self.assertIn('nested', all_config)
        self.assertEqual(all_config['key1'], 'value1')
        self.assertEqual(all_config['nested']['key'], 'nested_value')
    
    def test_clear_config(self):
        """Test clearing configuration."""
        # Set some values
        self.config_manager.set('key1', 'value1')
        self.config_manager.set('key2', 'value2')
        
        # Verify values exist
        self.assertTrue(self.config_manager.has('key1'))
        self.assertTrue(self.config_manager.has('key2'))
        
        # Clear and verify values are gone
        self.config_manager.clear()
        self.assertFalse(self.config_manager.has('key1'))
        self.assertFalse(self.config_manager.has('key2'))
    
    def test_save_config(self):
        """Test saving configuration to file."""
        # Set some configuration
        self.config_manager.set('save_key', 'save_value')
        self.config_manager.set('nested.save_key', 'nested_save_value')
        
        # Save to JSON file
        save_file = os.path.join(self.temp_dir, 'saved.json')
        self.config_manager.save_config(save_file, ConfigFormat.JSON)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(save_file))
        
        with open(save_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['save_key'], 'save_value')
        self.assertEqual(saved_data['nested']['save_key'], 'nested_save_value')
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Define validation schema
        schema = {
            'database': {
                'host': {'type': 'string', 'required': True},
                'port': {'type': 'integer', 'required': True, 'min': 1, 'max': 65535}
            }
        }
        
        # Valid configuration
        valid_config = {
            'database': {
                'host': 'localhost',
                'port': 5432
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'valid.json')
        with open(json_file, 'w') as f:
            json.dump(valid_config, f)
        
        # Should load without error
        self.config_manager.load_config(json_file, validation_schema=schema)
        
        # Invalid configuration
        invalid_config = {
            'database': {
                'host': 'localhost',
                'port': 'invalid_port'  # Should be integer
            }
        }
        
        invalid_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(invalid_file, 'w') as f:
            json.dump(invalid_config, f)
        
        # Should raise validation error
        with self.assertRaises(ValidationError):
            self.config_manager.load_config(invalid_file, validation_schema=schema)
    
    def test_config_transformation(self):
        """Test configuration transformation."""
        # Define transformation rules
        transformations = {
            'database.port': lambda x: int(x) if isinstance(x, str) else x,
            'features.debug': lambda x: x.lower() == 'true' if isinstance(x, str) else x
        }
        
        # Configuration with string values that need transformation
        config = {
            'database': {
                'port': '5432'  # String that should become int
            },
            'features': {
                'debug': 'true'  # String that should become bool
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'transform.json')
        with open(json_file, 'w') as f:
            json.dump(config, f)
        
        self.config_manager.load_config(json_file, transformations=transformations)
        
        # Verify transformations were applied
        self.assertEqual(
            self.config_manager.get('database.port'),
            5432  # Should be int, not string
        )
        self.assertTrue(
            self.config_manager.get('features.debug')  # Should be bool, not string
        )
    
    @patch('watchdog.observers.Observer')
    def test_watch_config_file(self, mock_observer):
        """Test configuration file watching."""
        # Create config file
        config_file = os.path.join(self.temp_dir, 'watched.json')
        with open(config_file, 'w') as f:
            json.dump(self.sample_config, f)
        
        # Mock observer
        mock_observer_instance = Mock()
        mock_observer.return_value = mock_observer_instance
        
        # Start watching
        self.config_manager.watch_config_file(config_file)
        
        # Verify observer was started
        mock_observer_instance.start.assert_called_once()
    
    def test_reload_config(self):
        """Test configuration reloading."""
        # Create initial config
        config_file = os.path.join(self.temp_dir, 'reload.json')
        initial_config = {'key': 'initial_value'}
        with open(config_file, 'w') as f:
            json.dump(initial_config, f)
        
        self.config_manager.load_config(config_file)
        self.assertEqual(self.config_manager.get('key'), 'initial_value')
        
        # Update config file
        updated_config = {'key': 'updated_value'}
        with open(config_file, 'w') as f:
            json.dump(updated_config, f)
        
        # Reload configuration
        self.config_manager.reload_config()
        
        # Verify updated value is loaded
        self.assertEqual(self.config_manager.get('key'), 'updated_value')


class TestEnvironmentManager(unittest.TestCase):
    """Test EnvironmentManager implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.env_manager = EnvironmentManager()
        
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        
        # Store original environment for cleanup
        self.original_env = dict(os.environ)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_implements_interface(self):
        """Test that EnvironmentManager implements IEnvironmentManager."""
        self.assertIsInstance(self.env_manager, IEnvironmentManager)
    
    def test_get_env_variable(self):
        """Test getting environment variable."""
        # Set test environment variable
        os.environ['TEST_VAR'] = 'test_value'
        
        # Get variable
        value = self.env_manager.get('TEST_VAR')
        self.assertEqual(value, 'test_value')
        
        # Get non-existent variable
        value = self.env_manager.get('NON_EXISTENT')
        self.assertIsNone(value)
        
        # Get with default
        value = self.env_manager.get('NON_EXISTENT', default='default_value')
        self.assertEqual(value, 'default_value')
    
    def test_set_env_variable(self):
        """Test setting environment variable."""
        # Set variable
        self.env_manager.set('NEW_VAR', 'new_value')
        
        # Verify it was set
        self.assertEqual(os.environ['NEW_VAR'], 'new_value')
        self.assertEqual(self.env_manager.get('NEW_VAR'), 'new_value')
    
    def test_delete_env_variable(self):
        """Test deleting environment variable."""
        # Set variable first
        os.environ['TO_DELETE'] = 'value'
        self.assertEqual(self.env_manager.get('TO_DELETE'), 'value')
        
        # Delete variable
        self.env_manager.delete('TO_DELETE')
        
        # Verify it was deleted
        self.assertNotIn('TO_DELETE', os.environ)
        self.assertIsNone(self.env_manager.get('TO_DELETE'))
    
    def test_has_env_variable(self):
        """Test checking if environment variable exists."""
        # Non-existent variable
        self.assertFalse(self.env_manager.has('NON_EXISTENT'))
        
        # Set and check existing variable
        os.environ['EXISTING_VAR'] = 'value'
        self.assertTrue(self.env_manager.has('EXISTING_VAR'))
    
    def test_get_all_env_variables(self):
        """Test getting all environment variables."""
        # Set some test variables
        os.environ['TEST_VAR1'] = 'value1'
        os.environ['TEST_VAR2'] = 'value2'
        
        all_vars = self.env_manager.get_all()
        
        # Should contain our test variables
        self.assertIn('TEST_VAR1', all_vars)
        self.assertIn('TEST_VAR2', all_vars)
        self.assertEqual(all_vars['TEST_VAR1'], 'value1')
        self.assertEqual(all_vars['TEST_VAR2'], 'value2')
    
    def test_get_filtered_env_variables(self):
        """Test getting filtered environment variables."""
        # Set test variables with prefix
        os.environ['APP_DATABASE_HOST'] = 'localhost'
        os.environ['APP_DATABASE_PORT'] = '5432'
        os.environ['APP_API_KEY'] = 'secret'
        os.environ['OTHER_VAR'] = 'other'
        
        # Get variables with APP_ prefix
        app_vars = self.env_manager.get_filtered(prefix='APP_')
        
        # Should contain only APP_ prefixed variables
        self.assertIn('APP_DATABASE_HOST', app_vars)
        self.assertIn('APP_DATABASE_PORT', app_vars)
        self.assertIn('APP_API_KEY', app_vars)
        self.assertNotIn('OTHER_VAR', app_vars)
        
        self.assertEqual(app_vars['APP_DATABASE_HOST'], 'localhost')
        self.assertEqual(app_vars['APP_API_KEY'], 'secret')
    
    def test_load_from_env_file(self):
        """Test loading environment variables from .env file."""
        # Create .env file
        env_file = os.path.join(self.temp_dir, '.env')
        env_content = """
# Database configuration
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=testdb

# API configuration
API_KEY=secret_key
API_TIMEOUT=30

# Features
DEBUG=true
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        # Load from file
        self.env_manager.load_from_file(env_file)
        
        # Verify variables were loaded
        self.assertEqual(self.env_manager.get('DATABASE_HOST'), 'localhost')
        self.assertEqual(self.env_manager.get('DATABASE_PORT'), '5432')
        self.assertEqual(self.env_manager.get('API_KEY'), 'secret_key')
        self.assertEqual(self.env_manager.get('DEBUG'), 'true')
        self.assertEqual(self.env_manager.get('LOG_LEVEL'), 'INFO')
    
    def test_load_from_env_file_with_override(self):
        """Test loading from .env file with override option."""
        # Set existing variable
        os.environ['EXISTING_VAR'] = 'original_value'
        
        # Create .env file with same variable
        env_file = os.path.join(self.temp_dir, '.env')
        with open(env_file, 'w') as f:
            f.write('EXISTING_VAR=new_value\n')
        
        # Load without override (should not change existing)
        self.env_manager.load_from_file(env_file, override=False)
        self.assertEqual(self.env_manager.get('EXISTING_VAR'), 'original_value')
        
        # Load with override (should change existing)
        self.env_manager.load_from_file(env_file, override=True)
        self.assertEqual(self.env_manager.get('EXISTING_VAR'), 'new_value')
    
    def test_expand_env_variables(self):
        """Test environment variable expansion."""
        # Set base variables
        os.environ['BASE_PATH'] = '/app'
        os.environ['ENV'] = 'production'
        
        # Test expansion
        expanded = self.env_manager.expand('${BASE_PATH}/logs/${ENV}.log')
        self.assertEqual(expanded, '/app/logs/production.log')
        
        # Test with default values
        expanded = self.env_manager.expand('${UNDEFINED_VAR:-default_value}')
        self.assertEqual(expanded, 'default_value')
        
        # Test nested expansion
        os.environ['LOG_DIR'] = '${BASE_PATH}/logs'
        expanded = self.env_manager.expand('${LOG_DIR}/${ENV}.log')
        self.assertEqual(expanded, '/app/logs/production.log')
    
    def test_validate_env_variables(self):
        """Test environment variable validation."""
        # Set test variables
        os.environ['REQUIRED_VAR'] = 'value'
        os.environ['NUMERIC_VAR'] = '123'
        os.environ['BOOLEAN_VAR'] = 'true'
        
        # Define validation rules
        validation_rules = {
            'REQUIRED_VAR': {'required': True},
            'NUMERIC_VAR': {'type': 'int', 'min': 100, 'max': 200},
            'BOOLEAN_VAR': {'type': 'bool'},
            'OPTIONAL_VAR': {'required': False, 'default': 'default_value'}
        }
        
        # Should validate successfully
        result = self.env_manager.validate(validation_rules)
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        
        # Test with invalid values
        os.environ['NUMERIC_VAR'] = 'not_a_number'
        
        result = self.env_manager.validate(validation_rules)
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_backup_and_restore_env(self):
        """Test environment backup and restore."""
        # Set initial state
        os.environ['BACKUP_TEST'] = 'initial_value'
        
        # Create backup
        backup_id = self.env_manager.backup()
        
        # Modify environment
        os.environ['BACKUP_TEST'] = 'modified_value'
        os.environ['NEW_VAR'] = 'new_value'
        
        # Verify changes
        self.assertEqual(self.env_manager.get('BACKUP_TEST'), 'modified_value')
        self.assertEqual(self.env_manager.get('NEW_VAR'), 'new_value')
        
        # Restore from backup
        self.env_manager.restore(backup_id)
        
        # Verify restoration
        self.assertEqual(self.env_manager.get('BACKUP_TEST'), 'initial_value')
        self.assertIsNone(self.env_manager.get('NEW_VAR'))


if __name__ == '__main__':
    unittest.main(verbosity=2)