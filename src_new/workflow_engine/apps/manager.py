"""Application manager for loading and managing app configurations."""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from ..utils.logger import get_logger
from .models import AppConfig, AppRunContext
from ..core.config import get_config

# Import and setup environment for module imports
from ..sdk.bootstrap import setup_environment

# Import Windows compatibility utilities
try:
    from ...utils.windows_compat import normalize_path, is_windows
except ImportError:
    # Fallback if windows_compat is not available
    def normalize_path(path):
        return Path(path)
    
    def is_windows():
        return os.name == 'nt'

logger = get_logger(__name__)


class AppManager:
    """Manages application configurations and lifecycle."""

    def __init__(self, apps_dir: Optional[str] = None):
        # Dynamic path resolution - determine the root module path
        self.root_module_path = self._determine_root_module_path()

        # Set apps directory using configuration system
        if apps_dir is None:
            # Use configuration system to get apps directory
            config = get_config()
            apps_dir_path = config.get_apps_directory_path()

            # Convert to absolute path if it's relative
            if not apps_dir_path.is_absolute():
                # Get project root (parent of src_new)
                project_root = Path(__file__).parent.parent.parent.parent
                apps_dir_path = project_root / apps_dir_path
        else:
            apps_dir_path = Path(apps_dir)
            # Convert to absolute path if it's relative
            if not apps_dir_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent.parent
                apps_dir_path = project_root / apps_dir_path

        self.apps_dir = normalize_path(apps_dir_path)

        # Backward compatibility: Check for legacy apps directory
        self._check_legacy_apps_directory()

        self.apps: Dict[str, AppConfig] = {}
        self._load_apps()

    def _determine_root_module_path(self) -> str:
        """Dynamically determine the root module path based on current module location."""
        # Get the current module's path
        current_module = sys.modules[self.__class__.__module__]
        current_file = normalize_path(current_module.__file__)

        # Navigate up to find the root module
        # Current structure: <root>/workflow_engine/apps/manager.py
        # We want to get to <root>
        root_path = current_file.parent.parent.parent

        # Convert to module path format
        root_module_name = root_path.name

        logger.debug(f"Determined root module path: {root_module_name}")
        return root_module_name

    def _check_legacy_apps_directory(self):
        """Check for legacy apps directory and provide migration warnings."""
        try:
            # Get project root (parent of src_new)
            project_root = Path(__file__).parent.parent.parent.parent
            legacy_apps_dir = normalize_path(project_root / "src_new" / "apps")

            # Check if legacy directory exists and has content
            if legacy_apps_dir.exists() and any(legacy_apps_dir.iterdir()):
                # Count apps in legacy directory
                legacy_app_count = 0
                for item in legacy_apps_dir.iterdir():
                    if item.is_dir() and (item / "app.json").exists():
                        legacy_app_count += 1

                if legacy_app_count > 0:
                    logger.warning("=" * 80)
                    logger.warning("🚨 LEGACY APPS DIRECTORY DETECTED")
                    logger.warning("=" * 80)
                    logger.warning(f"Found {legacy_app_count} app(s) in legacy directory: {legacy_apps_dir}")
                    logger.warning(f"Current apps directory: {self.apps_dir}")
                    logger.warning("")
                    logger.warning("📋 MIGRATION REQUIRED:")
                    logger.warning("1. Move apps from src_new/apps/ to apps/ (project root)")
                    logger.warning("2. Update app.json entry_point format:")
                    logger.warning("   OLD: 'apps.sample_app.flow1.imp.workflow_definition:create_flow1_workflow'")
                    logger.warning("   NEW: 'sample_app.flow1.imp.workflow_definition:create_flow1_workflow'")
                    logger.warning("3. Verify WORKFLOW_APPS_DIR environment variable points to 'apps'")
                    logger.warning("")
                    logger.warning("⚠️  The legacy directory will be ignored in future versions.")
                    logger.warning("=" * 80)

                    # Count apps in current directory for comparison
                    current_app_count = 0
                    if self.apps_dir.exists():
                        for item in self.apps_dir.iterdir():
                            if item.is_dir() and (item / "app.json").exists():
                                current_app_count += 1

                    if current_app_count == 0:
                        logger.error("❌ No apps found in current directory. Please migrate from legacy directory!")
                    elif current_app_count < legacy_app_count:
                        logger.warning(f"⚠️  Current directory has {current_app_count} apps, but legacy has {legacy_app_count}. Some apps may not be migrated.")

        except Exception as e:
            logger.debug(f"Error checking legacy apps directory: {e}")
            # Don't fail initialization due to legacy check errors

    def _load_apps(self):
        """Load all application configurations from apps directory."""
        if not self.apps_dir.exists():
            logger.warning(f"Apps directory not found: {self.apps_dir}")
            return

        logger.info(f"Loading applications from: {self.apps_dir}")

        # Look for app.json files in subdirectories
        for app_dir in self.apps_dir.iterdir():
            if app_dir.is_dir():
                config_file = normalize_path(app_dir / "app.json")
                if config_file.exists():
                    try:
                        self._load_app_config(config_file)
                    except Exception as e:
                        logger.error(f"Failed to load app config from {config_file}: {e}")

        # Also check for app.json in root apps directory
        root_config = normalize_path(self.apps_dir / "app.json")
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

        # Handle flow_ids field specially to avoid dataclass conflicts
        flow_ids_data = config_data.pop('flow_ids', None)

        app_config = AppConfig(**config_data)

        # Set flow_ids after initialization if present
        if flow_ids_data is not None:
            app_config._flow_ids = flow_ids_data

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
            # Setup environment to ensure proper Python path configuration
            setup_environment()

            # Parse entry point: module_path:function_name
            if ':' not in entry_point:
                raise ValueError(f"Invalid entry point format: {entry_point}")

            module_path, function_name = entry_point.split(':', 1)

            # Import the module
            module = __import__(module_path, fromlist=[function_name])

            # Try to import nodes module if it exists
            nodes_imported = False
            try:
                nodes_module_path = f"{module_path.rsplit('.', 1)[0]}.nodes"
                __import__(nodes_module_path)
                nodes_imported = True
                logger.debug(f"Successfully imported nodes module: {nodes_module_path}")
            except ImportError as e:
                logger.debug(f"No nodes module found at {nodes_module_path}: {e}")
                
                # Try alternative paths
                alternative_paths = [
                    f"{app_id}.nodes",
                    f"{app_id}.{flow_id}.nodes"
                ]
                
                for alt_path in alternative_paths:
                    try:
                        __import__(alt_path)
                        nodes_imported = True
                        logger.debug(f"Successfully imported nodes module: {alt_path}")
                        break
                    except ImportError:
                        logger.debug(f"No nodes module found at {alt_path}")
                
                if not nodes_imported:
                    logger.error(f"❌ All attempts to import nodes module failed for {app_id}.{flow_id}")
                    # Don't raise an exception here, let the workflow continue and fail later if functions are missing

            workflow_function = getattr(module, function_name)

            # Execute workflow definition function
            workflow_definition = workflow_function()

            logger.info(f"Loaded workflow definition for {app_id}.{flow_id}")
            return workflow_definition

        except Exception as e:
            logger.error(f"Failed to load workflow definition for {app_id}.{flow_id}: {e}")
            raise

    def load_workflow_metadata(self, app_id: str, flow_id: str) -> Optional[Dict]:
        """Load workflow metadata for a specific flow.

        优化：直接从 WorkflowDefinition 自动提取元数据，避免重复定义。
        基本信息从 app.json 获取，节点信息从工作流定义中提取。
        """
        try:
            # 从 app.json 获取基本信息
            app_config = self.get_app(app_id)
            if not app_config:
                logger.warning(f"App not found: {app_id}")
                return None

            # 获取工作流定义来提取节点信息
            try:
                workflow_definition = self.load_workflow_definition(app_id, flow_id)
                
                # 从工作流定义中提取节点信息
                nodes_info = []
                if hasattr(workflow_definition, 'nodes'):
                    for node in workflow_definition.nodes:
                        node_info = {
                            "id": getattr(node, 'id', 'unknown'),
                            "type": node.__class__.__name__,
                            "name": getattr(node, 'name', node.__class__.__name__)
                        }
                        
                        # 添加节点描述（如果有的话）
                        if hasattr(node, 'description'):
                            node_info["description"] = node.description
                        elif hasattr(node, '__doc__') and node.__doc__:
                            node_info["description"] = node.__doc__.strip().split('\n')[0]
                        
                        nodes_info.append(node_info)

                # 构建元数据
                metadata = {
                    "app_id": app_id,
                    "flow_id": flow_id,
                    "name": getattr(app_config, 'name', app_id),
                    "description": getattr(app_config, 'description', ''),
                    "version": getattr(app_config, 'version', '1.0.0'),
                    "author": getattr(app_config, 'author', ''),
                    "nodes": nodes_info,
                    "node_count": len(nodes_info),
                    "generated_at": datetime.now().isoformat()
                }

                # 如果有流特定的配置，添加流信息
                if hasattr(app_config, 'flows') and app_config.flows and flow_id in app_config.flows:
                    flow_config = app_config.flows[flow_id]
                    metadata.update({
                        "flow_description": getattr(flow_config, 'description', ''),
                        "flow_version": getattr(flow_config, 'version', '1.0.0'),
                        "flow_enabled": getattr(flow_config, 'enabled', True)
                    })

                return metadata

            except Exception as e:
                logger.warning(f"Failed to load workflow definition for metadata extraction: {e}")
                
                # 回退到基本元数据
                return {
                    "app_id": app_id,
                    "flow_id": flow_id,
                    "name": getattr(app_config, 'name', app_id),
                    "description": getattr(app_config, 'description', ''),
                    "version": getattr(app_config, 'version', '1.0.0'),
                    "author": getattr(app_config, 'author', ''),
                    "nodes": [],
                    "node_count": 0,
                    "generated_at": datetime.now().isoformat(),
                    "error": f"Failed to extract workflow definition: {str(e)}"
                }

        except Exception as e:
            logger.error(f"Failed to load workflow metadata for {app_id}.{flow_id}: {e}")
            return None