"""
Configuration Management Module

Handles project configuration and settings.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from .project_detector import ProjectTypeDetector

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages project configuration files and settings."""
    
    def __init__(self, project_root: Path):
        """Initialize configuration manager."""
        self.project_root = Path(project_root)
        self.config_dir = self.project_root / ".specify" / "config"
        self.speckit_config_file = self.config_dir / "speckit.json"
        self.local_config_file = self.project_root / ".speckitrc"
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_type: str = "all") -> Dict[str, Any]:
        """
        Load configuration from files.
        
        Args:
            config_type: Type of config to load ("speckit", "local", "all")
            
        Returns:
            Configuration dictionary
        """
        config = {}
        
        if config_type in ["speckit", "all"]:
            config.update(self._load_speckit_config())
            
        if config_type in ["local", "all"]:
            config.update(self._load_local_config())
            
        return config
    
    def save_config(self, config: Dict[str, Any], config_type: str = "speckit") -> bool:
        """
        Save configuration to files.
        
        Args:
            config: Configuration dictionary to save
            config_type: Type of config to save ("speckit", "local")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config_type == "speckit":
                return self._save_speckit_config(config)
            elif config_type == "local":
                return self._save_local_config(config)
            else:
                logger.error(f"Unknown config type: {config_type}")
                return False
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False
    
    def get_project_config(self) -> Dict[str, Any]:
        """Get project-specific configuration."""
        config = self.load_config("speckit")
        return config.get("project", {})
    
    def update_project_config(self, updates: Dict[str, Any]) -> bool:
        """Update project configuration."""
        config = self.load_config("speckit")
        if "project" not in config:
            config["project"] = {}
        
        config["project"].update(updates)
        return self.save_config(config, "speckit")
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """Get workflow configuration."""
        config = self.load_config("speckit")
        return config.get("workflow", {
            "default_sequence": ["constitution", "specify", "plan", "tasks", "implement"],
            "optional_commands": ["clarify", "analyze", "checklist"]
        })
    
    def get_integration_config(self) -> Dict[str, Any]:
        """Get integration configuration."""
        config = self.load_config("speckit")
        return config.get("integration", {
            "agent": "aone-copilot",
            "mode": "direct",
            "rules_file": ".aone_copilot/rules/default.md"
        })
    
    def get_deep_wiki_config(self) -> Dict[str, Any]:
        """Get Deep Wiki configuration."""
        deep_wiki_config_file = self.project_root / ".specify" / "deep-wiki" / "config.yml"
        
        if deep_wiki_config_file.exists():
            try:
                with open(deep_wiki_config_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Failed to load Deep Wiki config: {e}")
        
        return {}
    
    def update_deep_wiki_config(self, updates: Dict[str, Any]) -> bool:
        """Update Deep Wiki configuration."""
        deep_wiki_config_file = self.project_root / ".specify" / "deep-wiki" / "config.yml"
        deep_wiki_config_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load existing config
            existing_config = self.get_deep_wiki_config()
            existing_config.update(updates)
            
            # Save updated config
            with open(deep_wiki_config_file, 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, default_flow_style=False, allow_unicode=True)
            
            return True
        except Exception as e:
            logger.error(f"Failed to update Deep Wiki config: {e}")
            return False
    
    def get_directories_config(self) -> Dict[str, str]:
        """Get directory configuration."""
        config = self.load_config("speckit")
        return config.get("directories", {
            "specs": "specs/",
            "templates": ".specify/templates/",
            "scripts": ".specify/scripts/bash/",
            "memory": ".specify/memory/",
            "commands": ".cursor/commands/"
        })
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration data."""
        return {
            "project": self.get_project_config(),
            "workflow": self.get_workflow_config(),
            "integration": self.get_integration_config(),
            "directories": self.get_directories_config(),
            "deep_wiki": self.get_deep_wiki_config()
        }
    
    def _load_speckit_config(self) -> Dict[str, Any]:
        """Load Spec Kit JSON configuration."""
        if not self.speckit_config_file.exists():
            return self._create_default_speckit_config()
        
        try:
            with open(self.speckit_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load speckit config: {e}")
            return self._create_default_speckit_config()
    
    def _save_speckit_config(self, config: Dict[str, Any]) -> bool:
        """Save Spec Kit JSON configuration."""
        try:
            with open(self.speckit_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save speckit config: {e}")
            return False
    
    def _load_local_config(self) -> Dict[str, Any]:
        """Load local .speckitrc configuration."""
        if not self.local_config_file.exists():
            return {}
        
        config = {}
        try:
            with open(self.local_config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        config[key.strip()] = value
            return config
        except Exception as e:
            logger.warning(f"Failed to load local config: {e}")
            return {}
    
    def _save_local_config(self, config: Dict[str, Any]) -> bool:
        """Save local .speckitrc configuration."""
        try:
            with open(self.local_config_file, 'w', encoding='utf-8') as f:
                f.write("# Spec-Kit Project Configuration\n")
                for key, value in config.items():
                    f.write(f'{key}="{value}"\n')
            return True
        except Exception as e:
            logger.error(f"Failed to save local config: {e}")
            return False
    
    def _create_default_speckit_config(self) -> Dict[str, Any]:
        """Create default Spec Kit configuration."""
        project_name = self.project_root.name
        
        # Auto-detect project type
        detector = ProjectTypeDetector(self.project_root)
        detected_type, confidence = detector.detect_project_type()

        if confidence > 0.5:
            project_type = detected_type
            logger.info(f"Auto-detected project type for config: {project_type} (confidence: {confidence:.2f})")
        else:
            project_type = "java-spring-boot"  # fallback default
            logger.warning(f"Could not reliably detect project type for config (confidence: {confidence:.2f}), using default: {project_type}")

        default_config = {
            "version": "0.0.64",
            "project": {
                "name": project_name,
                "type": project_type,
                "constitution": ".specify/memory/constitution.md"
            },
            "directories": {
                "specs": "specs/",
                "templates": ".specify/templates/",
                "scripts": ".specify/scripts/bash/",
                "memory": ".specify/memory/",
                "commands": ".cursor/commands/"
            },
            "workflow": {
                "default_sequence": ["constitution", "specify", "plan", "tasks", "implement"],
                "optional_commands": ["clarify", "analyze", "checklist"]
            },
            "integration": {
                "agent": "aone-copilot",
                "mode": "direct",
                "rules_file": ".aone_copilot/rules/default.md"
            },
            "team": {
                "collaboration_mode": "spec-driven",
                "conflict_resolution": "specification-first",
                "review_required": True
            }
        }
        
        # Save the default config
        self._save_speckit_config(default_config)
        return default_config
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults."""
        try:
            # Remove existing config files
            if self.speckit_config_file.exists():
                self.speckit_config_file.unlink()
            if self.local_config_file.exists():
                self.local_config_file.unlink()
            
            # Recreate default config
            self._create_default_speckit_config()
            logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return validation results."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            config = self.load_config("all")
            
            # Check required fields
            required_fields = ["project.name", "project.type"]
            for field in required_fields:
                if not self._get_nested_value(config, field):
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["valid"] = False
            
            # Check directory structure
            directories = self.get_directories_config()
            for dir_name, dir_path in directories.items():
                full_path = self.project_root / dir_path
                if not full_path.exists():
                    validation_results["warnings"].append(f"Directory does not exist: {dir_path}")
            
            # Check constitution file
            constitution_path = self.project_root / ".specify" / "memory" / "constitution.md"
            if not constitution_path.exists():
                validation_results["warnings"].append("Constitution file not found")
            
        except Exception as e:
            validation_results["errors"].append(f"Configuration validation failed: {e}")
            validation_results["valid"] = False
        
        return validation_results
    
    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value