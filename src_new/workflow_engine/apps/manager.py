"""Application manager for loading and managing app configurations."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger
from .models import AppConfig, AppRunContext

logger = get_logger(__name__)

class AppManager:
    """Manages application configurations and lifecycle."""

    def __init__(self, apps_dir: str = "src_new/apps"):
        self.apps_dir = Path(apps_dir)
        self.apps: Dict[str, AppConfig] = {}
        self._load_apps()

    def _load_apps(self):
        """Load all application configurations from apps directory."""
        if not self.apps_dir.exists():
            logger.warning(f"Apps directory not found: {self.apps_dir}")
            return

        logger.info(f"Loading applications from: {self.apps_dir}")

        # Look for app.json files in subdirectories
        for app_dir in self.apps_dir.iterdir():
            if app_dir.is_dir():
                config_file = app_dir / "app.json"
                if config_file.exists():
                    try:
                        self._load_app_config(config_file)
                    except Exception as e:
                        logger.error(f"Failed to load app config from {config_file}: {e}")

        # Also check for app.json in root apps directory
        root_config = self.apps_dir / "app.json"
        if root_config.exists():
            try:
                self._load_app_config(root_config)
            except Exception as e:
                logger.error(f"Failed to load root app config from {root_config}: {e}")

        logger.info(f"Loaded {len(self.apps)} applications: {list(self.apps.keys())}")

    def _load_app_config(self, config_file: Path):
        """Load a single app configuration file."""
        logger.debug(f"Loading app config: {config_file}")

        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Add timestamps if not present
        if 'created_at' not in config_data:
            config_data['created_at'] = datetime.now().isoformat()
        if 'updated_at' not in config_data:
            config_data['updated_at'] = datetime.now().isoformat()

        app_config = AppConfig(**config_data)
        self.apps[app_config.app_id] = app_config

        logger.info(f"Loaded app: {app_config.app_id} ({app_config.name})")

    def get_app(self, app_id: str) -> Optional[AppConfig]:
        """Get application configuration by ID."""
        return self.apps.get(app_id)

    def list_apps(self) -> List[AppConfig]:
        """Get list of all loaded applications."""
        return list(self.apps.values())

    def get_all_apps(self) -> List[AppConfig]:
        """Get all loaded applications. Alias for list_apps()."""
        return self.list_apps()
    
    def get_app_by_flow(self, flow_id: str) -> Optional[AppConfig]:
        """Find application that contains the specified flow ID."""
        for app in self.apps.values():
            if flow_id in app.flow_ids or flow_id == app.default_flow_id:
                return app
        return None
    
    def parse_console_id(self, console_id: str) -> Optional[tuple[str, str]]:
        """Parse console ID into app_id and flow_id."""
        if '-' not in console_id:
            return None
        
        # Try to match against known app_ids first
        # This handles cases where app_id contains hyphens
        for app_id in self.apps.keys():
            if console_id.startswith(app_id + '-'):
                flow_id = console_id[len(app_id) + 1:]  # +1 for the hyphen
                if flow_id:  # Ensure flow_id is not empty
                    return app_id, flow_id

        # Fallback: simple split if no known app_id matches
        parts = console_id.split('-', 1)
        if len(parts) == 2:
            return parts[0], parts[1]

        return None
    
    def create_run_context(self, console_id: str, run_id: Optional[str] = None, 
                          thread_id: Optional[str] = None) -> Optional[AppRunContext]:
        """Create application run context from console ID."""
        parsed = self.parse_console_id(console_id)
        if not parsed:
            return None
        
        app_id, flow_id = parsed
        app_config = self.get_app(app_id)
        if not app_config:
            return None
        
        # Validate flow_id belongs to this app
        if flow_id not in app_config.flow_ids and flow_id != app_config.default_flow_id:
            logger.warning(f"Flow {flow_id} not associated with app {app_id}")
            return None
        
        return AppRunContext(
            app_config=app_config,
            flow_id=flow_id,
            run_id=run_id,
            thread_id=thread_id
        )
    
    def reload_apps(self):
        """Reload all application configurations."""
        self.apps.clear()
        self._load_apps()
    
    def validate_console_id(self, console_id: str) -> bool:
        """Validate if console ID is valid and app/flow exists."""
        context = self.create_run_context(console_id)
        return context is not None

    def get_flow_entry_point(self, app_id: str, flow_id: str) -> Optional[str]:
        """Get the entry point for a specific flow in an app."""
        app_config = self.get_app(app_id)
        if not app_config:
            return None

        # Check if app has flows configuration
        if hasattr(app_config, 'flows') and app_config.flows and flow_id in app_config.flows:
            return app_config.flows[flow_id].entry_point

        # Fallback to legacy entry_point if flow matches default
        if flow_id == app_config.default_flow_id and hasattr(app_config, 'entry_point'):
            return app_config.entry_point

        return None

    def get_flow_metadata_function(self, app_id: str, flow_id: str) -> Optional[str]:
        """Get the metadata function for a specific flow in an app."""
        app_config = self.get_app(app_id)
        if not app_config:
            return None

        # Check if app has flows configuration
        if hasattr(app_config, 'flows') and app_config.flows and flow_id in app_config.flows:
            return app_config.flows[flow_id].metadata_function

        return None

    def load_workflow_definition(self, app_id: str, flow_id: str):
        """Dynamically load workflow definition for a specific flow."""
        entry_point = self.get_flow_entry_point(app_id, flow_id)
        if not entry_point:
            raise ValueError(f"No entry point found for flow {flow_id} in app {app_id}")

        try:
            # Parse module and function name
            module_path, function_name = entry_point.split(':')

            # Dynamic import
            import importlib
            module = importlib.import_module(module_path)

            # Also import the nodes module to ensure decorators are executed
            # This registers the node functions in the function registry
            nodes_module_path = module_path.replace('.workflow_definition', '.nodes')
            try:
                importlib.import_module(nodes_module_path)
                logger.info(f"Imported nodes module: {nodes_module_path}")
            except ImportError as e:
                logger.warning(f"Could not import nodes module {nodes_module_path}: {e}")

            workflow_function = getattr(module, function_name)

            # Execute workflow definition function
            workflow_definition = workflow_function()

            logger.info(f"Loaded workflow definition for {app_id}.{flow_id}")
            return workflow_definition

        except Exception as e:
            logger.error(f"Failed to load workflow definition for {app_id}.{flow_id}: {e}")
            raise

    def load_workflow_metadata(self, app_id: str, flow_id: str) -> Optional[Dict]:
        """Load workflow metadata for a specific flow."""
        metadata_function = self.get_flow_metadata_function(app_id, flow_id)
        if not metadata_function:
            return None

        try:
            # Parse module and function name
            module_path, function_name = metadata_function.split(':')

            # Dynamic import
            import importlib
            module = importlib.import_module(module_path)
            metadata_function = getattr(module, function_name)

            # Execute metadata function
            metadata = metadata_function()

            logger.info(f"Loaded workflow metadata for {app_id}.{flow_id}")
            return metadata

        except Exception as e:
            logger.warning(f"Failed to load workflow metadata for {app_id}.{flow_id}: {e}")
            return None