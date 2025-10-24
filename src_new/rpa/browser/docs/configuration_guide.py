"""
Browser Automation Module - Configuration Guide

This module provides comprehensive documentation for all configuration parameters,
including descriptions, default values, validation rules, and usage examples.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum


class ConfigScope(Enum):
    """Configuration scopes in the system."""
    BROWSER = "browser"
    DOM_ANALYSIS = "dom_analysis"
    PAGINATION = "pagination"
    LOGGING = "logging"
    ENVIRONMENT = "environment"


class ConfigType(Enum):
    """Configuration parameter types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


@dataclass
class ConfigParameter:
    """Represents a single configuration parameter."""
    name: str
    type: ConfigType
    description: str
    default_value: Any
    required: bool = False
    validation_rules: Optional[Dict[str, Any]] = None
    examples: Optional[List[Any]] = None
    deprecated: bool = False
    since_version: Optional[str] = None


# Browser Configuration Parameters
BROWSER_CONFIG_PARAMETERS = [
    ConfigParameter(
        name="type",
        type=ConfigType.ENUM,
        description="Browser type to use for automation",
        default_value="chromium",
        required=False,
        validation_rules={
            "enum": ["chromium", "firefox", "webkit"],
            "case_sensitive": False
        },
        examples=["chromium", "firefox", "webkit"],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="headless",
        type=ConfigType.BOOLEAN,
        description="Run browser in headless mode (without GUI)",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="timeout",
        type=ConfigType.INTEGER,
        description="Default timeout for browser operations in milliseconds",
        default_value=30000,
        required=False,
        validation_rules={
            "min": 1000,
            "max": 300000,
            "type": "integer"
        },
        examples=[30000, 60000, 120000],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="viewport",
        type=ConfigType.OBJECT,
        description="Browser viewport size configuration",
        default_value={"width": 1920, "height": 1080},
        required=False,
        validation_rules={
            "properties": {
                "width": {"type": "integer", "min": 320, "max": 7680},
                "height": {"type": "integer", "min": 240, "max": 4320}
            },
            "required": ["width", "height"]
        },
        examples=[
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 375, "height": 667}  # Mobile viewport
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="user_agent",
        type=ConfigType.STRING,
        description="Custom user agent string for browser requests",
        default_value=None,
        required=False,
        validation_rules={
            "type": "string",
            "min_length": 10,
            "max_length": 500
        },
        examples=[
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="proxy",
        type=ConfigType.OBJECT,
        description="Proxy configuration for browser requests",
        default_value=None,
        required=False,
        validation_rules={
            "properties": {
                "server": {"type": "string", "pattern": r"^https?://.*:\d+$"},
                "username": {"type": "string"},
                "password": {"type": "string"}
            },
            "required": ["server"]
        },
        examples=[
            {"server": "http://proxy.example.com:8080"},
            {"server": "http://proxy.example.com:8080", "username": "user", "password": "pass"}
        ],
        since_version="1.1.0"
    ),
    
    ConfigParameter(
        name="retry_attempts",
        type=ConfigType.INTEGER,
        description="Number of retry attempts for failed operations",
        default_value=3,
        required=False,
        validation_rules={
            "min": 0,
            "max": 10,
            "type": "integer"
        },
        examples=[0, 3, 5],
        since_version="1.2.0"
    ),
    
    ConfigParameter(
        name="download_path",
        type=ConfigType.STRING,
        description="Default download directory for browser downloads",
        default_value=None,
        required=False,
        validation_rules={
            "type": "string",
            "path_exists": True
        },
        examples=["/tmp/downloads", "./downloads", "C:\\Downloads"],
        since_version="1.3.0"
    )
]


# DOM Analysis Configuration Parameters
DOM_ANALYSIS_CONFIG_PARAMETERS = [
    ConfigParameter(
        name="timeout",
        type=ConfigType.INTEGER,
        description="Timeout for DOM analysis operations in milliseconds",
        default_value=10000,
        required=False,
        validation_rules={
            "min": 1000,
            "max": 60000,
            "type": "integer"
        },
        examples=[5000, 10000, 30000],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="max_depth",
        type=ConfigType.INTEGER,
        description="Maximum depth for DOM tree traversal",
        default_value=10,
        required=False,
        validation_rules={
            "min": 1,
            "max": 50,
            "type": "integer"
        },
        examples=[5, 10, 20],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="extract_text",
        type=ConfigType.BOOLEAN,
        description="Extract text content from DOM elements",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="extract_links",
        type=ConfigType.BOOLEAN,
        description="Extract links (href attributes) from DOM elements",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="extract_images",
        type=ConfigType.BOOLEAN,
        description="Extract image information (src, alt attributes) from DOM elements",
        default_value=False,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="selectors",
        type=ConfigType.OBJECT,
        description="Custom CSS selectors for specific element extraction",
        default_value={},
        required=False,
        validation_rules={
            "type": "object",
            "additional_properties": {"type": "string"}
        },
        examples=[
            {"title": "h1, .title", "price": ".price, .cost"},
            {"product_name": ".product-title", "description": ".product-desc"}
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="ignore_hidden",
        type=ConfigType.BOOLEAN,
        description="Ignore hidden elements during DOM analysis",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.1.0"
    ),
    
    ConfigParameter(
        name="min_text_length",
        type=ConfigType.INTEGER,
        description="Minimum text length to include in extraction",
        default_value=1,
        required=False,
        validation_rules={
            "min": 0,
            "max": 1000,
            "type": "integer"
        },
        examples=[1, 5, 10],
        since_version="1.2.0"
    )
]


# Pagination Configuration Parameters
PAGINATION_CONFIG_PARAMETERS = [
    ConfigParameter(
        name="max_pages",
        type=ConfigType.INTEGER,
        description="Maximum number of pages to process",
        default_value=10,
        required=False,
        validation_rules={
            "min": 1,
            "max": 1000,
            "type": "integer"
        },
        examples=[5, 10, 50, 100],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="delay_between_pages",
        type=ConfigType.INTEGER,
        description="Delay between page transitions in milliseconds",
        default_value=2000,
        required=False,
        validation_rules={
            "min": 0,
            "max": 60000,
            "type": "integer"
        },
        examples=[1000, 2000, 5000],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="timeout",
        type=ConfigType.INTEGER,
        description="Timeout for pagination operations in milliseconds",
        default_value=30000,
        required=False,
        validation_rules={
            "min": 5000,
            "max": 300000,
            "type": "integer"
        },
        examples=[30000, 60000, 120000],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="strategies",
        type=ConfigType.ARRAY,
        description="Pagination strategies to attempt in order",
        default_value=["numeric"],
        required=False,
        validation_rules={
            "type": "array",
            "items": {"enum": ["numeric", "scroll", "load_more", "infinite_scroll"]},
            "min_items": 1,
            "max_items": 4
        },
        examples=[
            ["numeric"],
            ["numeric", "scroll"],
            ["load_more", "scroll"],
            ["numeric", "scroll", "load_more"]
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="selectors",
        type=ConfigType.OBJECT,
        description="CSS selectors for pagination elements",
        default_value={},
        required=False,
        validation_rules={
            "type": "object",
            "properties": {
                "next_button": {"type": "string"},
                "previous_button": {"type": "string"},
                "page_items": {"type": "string"},
                "load_more": {"type": "string"},
                "page_numbers": {"type": "string"}
            }
        },
        examples=[
            {"next_button": ".next", "page_items": ".item"},
            {"next_button": ".pagination-next", "page_items": ".product", "load_more": ".load-more"}
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="scroll_behavior",
        type=ConfigType.OBJECT,
        description="Configuration for scroll-based pagination",
        default_value={"distance": 1000, "pause_time": 1000},
        required=False,
        validation_rules={
            "type": "object",
            "properties": {
                "distance": {"type": "integer", "min": 100, "max": 10000},
                "pause_time": {"type": "integer", "min": 100, "max": 10000}
            }
        },
        examples=[
            {"distance": 1000, "pause_time": 1000},
            {"distance": 500, "pause_time": 2000}
        ],
        since_version="1.1.0"
    ),
    
    ConfigParameter(
        name="error_recovery",
        type=ConfigType.BOOLEAN,
        description="Enable error recovery for pagination failures",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.2.0"
    )
]


# Logging Configuration Parameters
LOGGING_CONFIG_PARAMETERS = [
    ConfigParameter(
        name="level",
        type=ConfigType.ENUM,
        description="Logging level for filtering log messages",
        default_value="INFO",
        required=False,
        validation_rules={
            "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        },
        examples=["DEBUG", "INFO", "WARNING", "ERROR"],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="format",
        type=ConfigType.ENUM,
        description="Log message format",
        default_value="json",
        required=False,
        validation_rules={
            "enum": ["json", "text", "structured"]
        },
        examples=["json", "text", "structured"],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="performance_tracking",
        type=ConfigType.BOOLEAN,
        description="Enable performance tracking and timing logs",
        default_value=False,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="file_output",
        type=ConfigType.BOOLEAN,
        description="Enable logging to file",
        default_value=False,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="file_config",
        type=ConfigType.OBJECT,
        description="File logging configuration",
        default_value={
            "filename": "browser_automation.log",
            "max_size": "10MB",
            "backup_count": 5
        },
        required=False,
        validation_rules={
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "max_size": {"type": "string", "pattern": r"^\d+[KMGT]?B$"},
                "backup_count": {"type": "integer", "min": 1, "max": 100}
            }
        },
        examples=[
            {"filename": "automation.log", "max_size": "10MB", "backup_count": 5},
            {"filename": "/var/log/browser.log", "max_size": "50MB", "backup_count": 10}
        ],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="console_output",
        type=ConfigType.BOOLEAN,
        description="Enable logging to console/stdout",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.1.0"
    ),
    
    ConfigParameter(
        name="error_tracking",
        type=ConfigType.BOOLEAN,
        description="Enable detailed error tracking and stack traces",
        default_value=True,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.2.0"
    ),
    
    ConfigParameter(
        name="metrics",
        type=ConfigType.ARRAY,
        description="List of metrics to track and log",
        default_value=["page_load_time", "dom_analysis_time"],
        required=False,
        validation_rules={
            "type": "array",
            "items": {"enum": ["page_load_time", "dom_analysis_time", "extraction_time", 
                              "pagination_time", "memory_usage", "cpu_usage"]}
        },
        examples=[
            ["page_load_time", "dom_analysis_time"],
            ["page_load_time", "memory_usage", "cpu_usage"]
        ],
        since_version="1.3.0"
    )
]


# Environment Configuration Parameters
ENVIRONMENT_CONFIG_PARAMETERS = [
    ConfigParameter(
        name="profile",
        type=ConfigType.ENUM,
        description="Environment profile (affects default values)",
        default_value="development",
        required=False,
        validation_rules={
            "enum": ["development", "testing", "staging", "production"]
        },
        examples=["development", "testing", "production"],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="debug_mode",
        type=ConfigType.BOOLEAN,
        description="Enable debug mode with verbose logging",
        default_value=False,
        required=False,
        validation_rules={
            "type": "boolean"
        },
        examples=[True, False],
        since_version="1.0.0"
    ),
    
    ConfigParameter(
        name="temp_directory",
        type=ConfigType.STRING,
        description="Temporary directory for browser data and downloads",
        default_value=None,
        required=False,
        validation_rules={
            "type": "string"
        },
        examples=["/tmp/browser_automation", "./temp", "C:\\Temp\\Browser"],
        since_version="1.1.0"
    ),
    
    ConfigParameter(
        name="max_memory_usage",
        type=ConfigType.STRING,
        description="Maximum memory usage limit",
        default_value="1GB",
        required=False,
        validation_rules={
            "type": "string",
            "pattern": r"^\d+[KMGT]?B$"
        },
        examples=["512MB", "1GB", "2GB"],
        since_version="1.2.0"
    )
]


# Configuration Scopes
CONFIGURATION_SCOPES = {
    ConfigScope.BROWSER: {
        "description": "Browser-specific configuration parameters",
        "parameters": BROWSER_CONFIG_PARAMETERS,
        "required": False,
        "examples": [
            {
                "type": "chromium",
                "headless": True,
                "timeout": 30000,
                "viewport": {"width": 1920, "height": 1080}
            },
            {
                "type": "firefox",
                "headless": False,
                "timeout": 60000,
                "user_agent": "Custom User Agent String"
            }
        ]
    },
    
    ConfigScope.DOM_ANALYSIS: {
        "description": "DOM analysis and content extraction configuration",
        "parameters": DOM_ANALYSIS_CONFIG_PARAMETERS,
        "required": False,
        "examples": [
            {
                "timeout": 10000,
                "extract_text": True,
                "extract_links": True,
                "selectors": {"title": "h1", "price": ".price"}
            },
            {
                "max_depth": 15,
                "extract_images": True,
                "ignore_hidden": False
            }
        ]
    },
    
    ConfigScope.PAGINATION: {
        "description": "Pagination handling and data extraction configuration",
        "parameters": PAGINATION_CONFIG_PARAMETERS,
        "required": False,
        "examples": [
            {
                "max_pages": 10,
                "delay_between_pages": 2000,
                "strategies": ["numeric", "scroll"],
                "selectors": {"next_button": ".next", "page_items": ".item"}
            },
            {
                "max_pages": 50,
                "strategies": ["load_more"],
                "selectors": {"load_more": ".load-more-btn"}
            }
        ]
    },
    
    ConfigScope.LOGGING: {
        "description": "Logging and monitoring configuration",
        "parameters": LOGGING_CONFIG_PARAMETERS,
        "required": False,
        "examples": [
            {
                "level": "INFO",
                "format": "json",
                "performance_tracking": True,
                "file_output": True
            },
            {
                "level": "DEBUG",
                "format": "text",
                "console_output": True,
                "error_tracking": True
            }
        ]
    },
    
    ConfigScope.ENVIRONMENT: {
        "description": "Environment-specific configuration",
        "parameters": ENVIRONMENT_CONFIG_PARAMETERS,
        "required": False,
        "examples": [
            {
                "profile": "production",
                "debug_mode": False,
                "max_memory_usage": "2GB"
            },
            {
                "profile": "development",
                "debug_mode": True,
                "temp_directory": "./temp"
            }
        ]
    }
}


# Configuration Templates
CONFIGURATION_TEMPLATES = {
    "minimal": {
        "description": "Minimal configuration with default values",
        "config": {
            "browser": {"type": "chromium", "headless": True},
            "logging": {"level": "INFO"}
        }
    },
    
    "development": {
        "description": "Development environment configuration",
        "config": {
            "browser": {
                "type": "chromium",
                "headless": False,
                "timeout": 30000
            },
            "dom_analysis": {
                "timeout": 10000,
                "extract_text": True,
                "extract_links": True
            },
            "pagination": {
                "max_pages": 5,
                "delay_between_pages": 1000
            },
            "logging": {
                "level": "DEBUG",
                "format": "text",
                "console_output": True,
                "performance_tracking": True
            },
            "environment": {
                "profile": "development",
                "debug_mode": True
            }
        }
    },
    
    "production": {
        "description": "Production environment configuration",
        "config": {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 60000,
                "retry_attempts": 3
            },
            "dom_analysis": {
                "timeout": 15000,
                "extract_text": True,
                "extract_links": True,
                "ignore_hidden": True
            },
            "pagination": {
                "max_pages": 100,
                "delay_between_pages": 2000,
                "error_recovery": True
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "file_output": True,
                "performance_tracking": True,
                "error_tracking": True
            },
            "environment": {
                "profile": "production",
                "debug_mode": False,
                "max_memory_usage": "2GB"
            }
        }
    },
    
    "high_performance": {
        "description": "High-performance configuration for large-scale operations",
        "config": {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 45000,
                "viewport": {"width": 1366, "height": 768}
            },
            "dom_analysis": {
                "timeout": 8000,
                "max_depth": 8,
                "extract_text": True,
                "extract_links": False,
                "ignore_hidden": True,
                "min_text_length": 5
            },
            "pagination": {
                "max_pages": 200,
                "delay_between_pages": 1500,
                "strategies": ["numeric", "scroll"]
            },
            "logging": {
                "level": "WARNING",
                "format": "json",
                "file_output": True,
                "performance_tracking": True,
                "metrics": ["page_load_time", "memory_usage"]
            }
        }
    },
    
    "testing": {
        "description": "Testing environment configuration",
        "config": {
            "browser": {
                "type": "chromium",
                "headless": True,
                "timeout": 10000
            },
            "dom_analysis": {
                "timeout": 5000,
                "extract_text": True,
                "extract_links": True
            },
            "pagination": {
                "max_pages": 2,
                "delay_between_pages": 500
            },
            "logging": {
                "level": "DEBUG",
                "format": "text",
                "console_output": True
            },
            "environment": {
                "profile": "testing",
                "debug_mode": True
            }
        }
    }
}


# Configuration Validation Rules
VALIDATION_RULES = {
    "cross_parameter_validation": [
        {
            "rule": "browser.timeout >= dom_analysis.timeout",
            "message": "Browser timeout must be greater than or equal to DOM analysis timeout"
        },
        {
            "rule": "browser.timeout >= pagination.timeout",
            "message": "Browser timeout must be greater than or equal to pagination timeout"
        },
        {
            "rule": "pagination.max_pages > 0",
            "message": "Maximum pages must be greater than 0"
        },
        {
            "rule": "logging.file_output == True implies logging.file_config is not None",
            "message": "File configuration is required when file output is enabled"
        }
    ],
    
    "environment_specific_rules": {
        "production": [
            {
                "rule": "browser.headless == True",
                "message": "Headless mode is required in production"
            },
            {
                "rule": "logging.level in ['INFO', 'WARNING', 'ERROR']",
                "message": "Debug logging is not recommended in production"
            }
        ],
        "development": [
            {
                "rule": "logging.performance_tracking == True",
                "message": "Performance tracking is recommended in development"
            }
        ]
    }
}


# Migration Guide for Configuration Changes
MIGRATION_GUIDE = {
    "1.0.0_to_1.1.0": {
        "changes": [
            "Added browser.proxy configuration",
            "Added dom_analysis.ignore_hidden parameter",
            "Added pagination.scroll_behavior configuration",
            "Added logging.console_output parameter"
        ],
        "breaking_changes": [],
        "migration_steps": [
            "Update configuration files to include new optional parameters",
            "Review proxy settings if using corporate networks",
            "Consider enabling ignore_hidden for better performance"
        ]
    },
    
    "1.1.0_to_1.2.0": {
        "changes": [
            "Added browser.retry_attempts parameter",
            "Added dom_analysis.min_text_length parameter",
            "Added pagination.error_recovery parameter",
            "Added logging.error_tracking parameter",
            "Added environment.max_memory_usage parameter"
        ],
        "breaking_changes": [],
        "migration_steps": [
            "Review retry settings for production environments",
            "Adjust min_text_length based on content requirements",
            "Enable error_recovery for robust pagination"
        ]
    }
}


def get_parameter_by_name(scope: ConfigScope, parameter_name: str) -> Optional[ConfigParameter]:
    """Get a specific configuration parameter by scope and name."""
    scope_config = CONFIGURATION_SCOPES.get(scope)
    if not scope_config:
        return None
    
    for param in scope_config["parameters"]:
        if param.name == parameter_name:
            return param
    return None


def get_parameters_by_scope(scope: ConfigScope) -> List[ConfigParameter]:
    """Get all parameters for a specific configuration scope."""
    scope_config = CONFIGURATION_SCOPES.get(scope)
    return scope_config["parameters"] if scope_config else []


def get_template_config(template_name: str) -> Optional[Dict[str, Any]]:
    """Get a configuration template by name."""
    template = CONFIGURATION_TEMPLATES.get(template_name)
    return template["config"] if template else None


def validate_configuration(config: Dict[str, Any], environment: str = "development") -> List[str]:
    """Validate a configuration against all rules."""
    errors = []
    
    # Validate individual parameters
    for scope_name, scope_config in config.items():
        try:
            scope_enum = ConfigScope(scope_name)
            parameters = get_parameters_by_scope(scope_enum)
            
            for param in parameters:
                if param.name in scope_config:
                    value = scope_config[param.name]
                    param_errors = validate_parameter(param, value)
                    errors.extend([f"{scope_name}.{param.name}: {error}" for error in param_errors])
        except ValueError:
            errors.append(f"Unknown configuration scope: {scope_name}")
    
    # Cross-parameter validation
    for rule in VALIDATION_RULES["cross_parameter_validation"]:
        if not evaluate_rule(rule["rule"], config):
            errors.append(rule["message"])
    
    # Environment-specific validation
    env_rules = VALIDATION_RULES["environment_specific_rules"].get(environment, [])
    for rule in env_rules:
        if not evaluate_rule(rule["rule"], config):
            errors.append(f"Environment '{environment}': {rule['message']}")
    
    return errors


def validate_parameter(param: ConfigParameter, value: Any) -> List[str]:
    """Validate a single parameter value."""
    errors = []
    
    if param.validation_rules:
        rules = param.validation_rules
        
        # Type validation
        if "type" in rules:
            expected_type = rules["type"]
            if not validate_type(value, expected_type):
                errors.append(f"Expected {expected_type}, got {type(value).__name__}")
        
        # Enum validation
        if "enum" in rules:
            if value not in rules["enum"]:
                errors.append(f"Value must be one of {rules['enum']}")
        
        # Range validation
        if "min" in rules and isinstance(value, (int, float)):
            if value < rules["min"]:
                errors.append(f"Value must be >= {rules['min']}")
        
        if "max" in rules and isinstance(value, (int, float)):
            if value > rules["max"]:
                errors.append(f"Value must be <= {rules['max']}")
        
        # String validation
        if isinstance(value, str):
            if "min_length" in rules and len(value) < rules["min_length"]:
                errors.append(f"String length must be >= {rules['min_length']}")
            
            if "max_length" in rules and len(value) > rules["max_length"]:
                errors.append(f"String length must be <= {rules['max_length']}")
            
            if "pattern" in rules:
                import re
                if not re.match(rules["pattern"], value):
                    errors.append(f"String must match pattern: {rules['pattern']}")
    
    return errors


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate that a value matches the expected type."""
    type_mapping = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "array": list,
        "object": dict
    }
    
    expected_python_type = type_mapping.get(expected_type)
    if not expected_python_type:
        return False
    
    return isinstance(value, expected_python_type)


def evaluate_rule(rule: str, config: Dict[str, Any]) -> bool:
    """Evaluate a validation rule against configuration."""
    # This is a simplified rule evaluator
    # In a real implementation, you'd want a more robust expression parser
    try:
        # Replace configuration references with actual values
        rule_expr = rule
        for scope, scope_config in config.items():
            for param, value in scope_config.items():
                rule_expr = rule_expr.replace(f"{scope}.{param}", str(value))
        
        # Simple evaluation (in production, use a safer expression evaluator)
        return eval(rule_expr)
    except:
        return True  # Default to valid if rule evaluation fails


def generate_configuration_documentation() -> str:
    """Generate comprehensive configuration documentation."""
    doc = []
    doc.append("# Browser Automation Configuration Guide")
    doc.append("=" * 50)
    doc.append("")
    
    # Configuration Scopes
    doc.append("## Configuration Scopes")
    doc.append("")
    for scope, scope_info in CONFIGURATION_SCOPES.items():
        doc.append(f"### {scope.value}")
        doc.append(f"**Description**: {scope_info['description']}")
        doc.append("")
        
        # Parameters
        doc.append("#### Parameters")
        doc.append("")
        for param in scope_info["parameters"]:
            doc.append(f"**{param.name}** ({param.type.value})")
            doc.append(f"- Description: {param.description}")
            doc.append(f"- Default: {param.default_value}")
            doc.append(f"- Required: {param.required}")
            if param.examples:
                doc.append(f"- Examples: {param.examples}")
            doc.append("")
    
    # Configuration Templates
    doc.append("## Configuration Templates")
    doc.append("")
    for template_name, template_info in CONFIGURATION_TEMPLATES.items():
        doc.append(f"### {template_name}")
        doc.append(f"**Description**: {template_info['description']}")
        doc.append("```json")
        import json
        doc.append(json.dumps(template_info["config"], indent=2))
        doc.append("```")
        doc.append("")
    
    return "\n".join(doc)


if __name__ == "__main__":
    print("Browser Automation Module - Configuration Guide")
    print("=" * 50)
    
    print(f"Configuration Scopes: {len(CONFIGURATION_SCOPES)}")
    for scope in CONFIGURATION_SCOPES.keys():
        scope_info = CONFIGURATION_SCOPES[scope]
        param_count = len(scope_info["parameters"])
        print(f"  {scope.value}: {param_count} parameters")
    
    print(f"\nConfiguration Templates: {len(CONFIGURATION_TEMPLATES)}")
    for template_name, template_info in CONFIGURATION_TEMPLATES.items():
        print(f"  {template_name}: {template_info['description']}")
    
    print(f"\nValidation Rules: {len(VALIDATION_RULES['cross_parameter_validation'])}")
    print(f"Environment-specific Rules: {len(VALIDATION_RULES['environment_specific_rules'])}")
    
    # Example validation
    print("\nExample Configuration Validation:")
    test_config = CONFIGURATION_TEMPLATES["development"]["config"]
    errors = validate_configuration(test_config, "development")
    if errors:
        print(f"  Validation errors: {errors}")
    else:
        print("  Configuration is valid!")