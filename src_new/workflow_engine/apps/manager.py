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

            # Generate possible nodes module paths
            possible_nodes_paths = [
                # Direct replacement: apps.sample_app.flow1.imp.workflow_definition -> apps.sample_app.flow1.imp.nodes
                module_path.replace('.workflow_definition', '.nodes'),
                # Remove workflow_definition and add nodes: apps.sample_app.flow1.imp.workflow_definition -> apps.sample_app.flow1.imp.nodes
                f"{module_path.rsplit('.', 1)[0]}.nodes",
                # Try without imp: apps.sample_app.flow1.imp.workflow_definition -> apps.sample_app.flow1.nodes
                f"{'.'.join(module_path.split('.')[:-2])}.nodes",
                # Try with different structure: apps.sample_app.flow1.imp.workflow_definition -> apps.sample_app.flow1.nodes
                module_path.replace('.imp.workflow_definition', '.nodes'),
            ]

            nodes_imported = False
            for nodes_module_path in possible_nodes_paths:
                try:
                    logger.info(f"🔍 Trying to import nodes module: {nodes_module_path}")
                    nodes_module = importlib.import_module(nodes_module_path)
                    logger.info(f"✅ Successfully imported nodes module: {nodes_module_path}")

                    # Force reload to ensure decorators are executed
                    importlib.reload(nodes_module)
                    logger.info(f"✅ Reloaded nodes module to ensure function registration")

                    nodes_imported = True
                    break

                except ImportError as e:
                    logger.debug(f"Could not import nodes module {nodes_module_path}: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error importing nodes module {nodes_module_path}: {e}")
                    continue

            if not nodes_imported:
                logger.error(f"❌ Failed to import any nodes module for {app_id}.{flow_id}")
                logger.error(f"Tried paths: {possible_nodes_paths}")

                # As a last resort, try to find nodes.py files in the app directory
                try:
                    import os
                    from pathlib import Path

                    # Get the app directory path
                    app_parts = module_path.split('.')
                    if len(app_parts) >= 3:  # apps.sample_app.flow1...
                        app_dir = Path("src_new") / "apps" / app_parts[1] / app_parts[2] / "imp"
                        nodes_file = app_dir / "nodes.py"

                        if nodes_file.exists():
                            logger.info(f"🔍 Found nodes.py file at: {nodes_file}")
                            # Try to construct the correct import path
                            correct_path = f"apps.{app_parts[1]}.{app_parts[2]}.imp.nodes"
                            try:
                                nodes_module = importlib.import_module(correct_path)
                                importlib.reload(nodes_module)
                                logger.info(f"✅ Successfully imported nodes using constructed path: {correct_path}")
                                nodes_imported = True
                            except Exception as e:
                                logger.error(f"Failed to import with constructed path {correct_path}: {e}")
                        else:
                            logger.warning(f"nodes.py file not found at expected location: {nodes_file}")
                except Exception as e:
                    logger.error(f"Error in fallback nodes import logic: {e}")

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

            # 获取工作流基本信息
            flow_config = None
            if hasattr(app_config, 'flows') and app_config.flows and flow_id in app_config.flows:
                flow_config = app_config.flows[flow_id]

            if not flow_config:
                logger.warning(f"Flow config not found: {app_id}.{flow_id}")
                return None

            # 加载工作流定义以提取节点信息
            workflow_definition = self.load_workflow_definition(app_id, flow_id)
            if not workflow_definition:
                logger.warning(f"Could not load workflow definition for {app_id}.{flow_id}")
                return None

            # 自动从 WorkflowDefinition 提取节点元数据
            nodes_metadata = {}
            for node in workflow_definition.nodes:
                node_info = {
                    "type": node.type.value,
                    "id": node.id
                }

                # 根据节点类型提取详细信息
                if node.type.value == "python" and node.data:
                    node_info.update({
                        "function_ref": node.data.code_ref,
                        "parameters": node.data.args
                    })
                elif node.type.value == "condition" and node.data:
                    node_info.update({
                        "condition": node.data.expr
                    })

                nodes_metadata[node.id] = node_info

            # 构建完整的元数据（基本信息来自 app.json，节点信息自动提取）
            metadata = {
                "nodes": nodes_metadata,
                "technical_info": {
                    "total_nodes": len(workflow_definition.nodes),
                    "total_edges": len(workflow_definition.edges),
                    "node_types": list(set(node.type.value for node in workflow_definition.nodes)),
                    "auto_generated": True,
                    "source": "extracted_from_workflow_definition"
                }
            }

            logger.info(f"Auto-generated workflow metadata for {app_id}.{flow_id} with {len(nodes_metadata)} nodes")
            return metadata

        except Exception as e:
            logger.warning(f"Failed to auto-generate workflow metadata for {app_id}.{flow_id}: {e}")

            # 降级：尝试使用传统的 metadata_function 方式
            metadata_function = self.get_flow_metadata_function(app_id, flow_id)
            if metadata_function:
                try:
                    # Parse module and function name
                    module_path, function_name = metadata_function.split(':')

                    # Dynamic import
                    import importlib
                    module = importlib.import_module(module_path)
                    metadata_function_obj = getattr(module, function_name)

                    # Execute metadata function
                    metadata = metadata_function_obj()

                    logger.info(f"Loaded workflow metadata using legacy method for {app_id}.{flow_id}")
                    return metadata

                except Exception as legacy_e:
                    logger.warning(f"Legacy metadata loading also failed for {app_id}.{flow_id}: {legacy_e}")

            return None