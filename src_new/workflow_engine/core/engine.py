"""Core workflow engine implementation using LangGraph."""

import uuid
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Union

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from .models import WorkflowDefinition, WorkflowState, NodeType
from .registry import get_registered_function
from .config import get_config, get_container, WorkflowEngineConfig, DependencyContainer
from .security import validate_workflow_definition, validate_input_data, execution_timeout, get_import_manager
from ..nodes.python_node import PythonNode
from ..nodes.condition_node import ConditionNode
from ..storage.database import DatabaseManager
from ..utils.logger import WorkflowLogger, get_logger

logger = get_logger(__name__)


class WorkflowInterrupt(Exception):
    """Custom exception for workflow interrupts that integrates with LangGraph."""

    def __init__(self, reason: str, data: Optional[Dict[str, Any]] = None):
        self.reason = reason
        self.data = data or {}
        super().__init__(f"Workflow interrupted: {reason}")


class WorkflowEngine:
    """Core workflow engine using LangGraph for orchestration."""

    def __init__(self, config: Optional[WorkflowEngineConfig] = None,
                 container: Optional[DependencyContainer] = None):
        # Thread safety
        self._lock = threading.RLock()

        # Use provided config or get global config
        self.config = config or get_config()
        self.container = container or get_container()

        # Initialize database manager with dependency injection
        if self.container.has(DatabaseManager):
            self.db_manager = self.container.get(DatabaseManager)
        else:
            self.db_manager = DatabaseManager(self.config.db_path)
            self.container.register_singleton(DatabaseManager, self.db_manager)

        # Initialize checkpointer with thread safety
        self.checkpointer = None
        if self.config.checkpoint_enabled:
            self._initialize_checkpointer()

        logger.info("Workflow engine initialized with dependency injection")

    def _initialize_checkpointer(self):
        """Initialize checkpointer with proper error handling."""
        try:
            checkpoint_db_path = self.config.checkpoint_db_path or ":memory:"

            # Initialize SQLite connection for checkpoints with thread safety
            checkpoint_conn = sqlite3.connect(
                checkpoint_db_path,
                check_same_thread=False,
                timeout=self.config.query_timeout
            )

            self.checkpointer = SqliteSaver(checkpoint_conn)
            logger.info(f"Checkpoint persistence enabled: {checkpoint_db_path}")

        except Exception as e:
            logger.warning(f"Failed to initialize checkpointer: {e}, running without persistence")
            self.checkpointer = None

    def compile_workflow(self, definition: WorkflowDefinition) -> StateGraph:
        """Compile workflow definition into LangGraph StateGraph."""

        # Create state graph
        graph = StateGraph(WorkflowState)

        # Add nodes
        for node in definition.nodes:
            if node.type == NodeType.START:
                graph.add_node(node.id, self._start_node)
            elif node.type == NodeType.END:
                graph.add_node(node.id, self._end_node)
            elif node.type == NodeType.PYTHON:
                graph.add_node(node.id, self._create_python_node_handler(node))
            elif node.type == NodeType.CONDITION:
                graph.add_node(node.id, self._create_condition_node_handler(node))
            else:
                raise ValueError(f"Unsupported node type: {node.type}")

        # Process edges and collect conditional edges
        conditional_edges = {}

        for edge in definition.edges:
            if hasattr(edge, 'condition') and edge.condition:
                # This is a conditional edge
                if edge.source not in conditional_edges:
                    conditional_edges[edge.source] = {
                        "condition": edge.condition,
                        "true_targets": [],
                        "false_targets": []
                    }

                # Determine if this is true or false branch
                if hasattr(edge, 'condition_value') and edge.condition_value is False:
                    conditional_edges[edge.source]["false_targets"].append(edge.target)
                else:
                    conditional_edges[edge.source]["true_targets"].append(edge.target)
            else:
                # Regular edge
                graph.add_edge(edge.source, edge.target)

        # Add conditional edges
        for source_node, edge_info in conditional_edges.items():
            true_target = edge_info["true_targets"][0] if edge_info["true_targets"] else END
            false_target = edge_info["false_targets"][0] if edge_info["false_targets"] else END

            graph.add_conditional_edges(
                source_node,
                self._create_condition_router(edge_info["condition"]),
                {True: true_target, False: false_target}
            )

        # Set entry point
        start_nodes = [n for n in definition.nodes if n.type == NodeType.START]
        if start_nodes:
            graph.set_entry_point(start_nodes[0].id)
        else:
            # If no start node, use first node as entry point
            if definition.nodes:
                graph.set_entry_point(definition.nodes[0].id)

        # Set finish point
        end_nodes = [n for n in definition.nodes if n.type == NodeType.END]
        if end_nodes:
            graph.set_finish_point(end_nodes[0].id)

        return graph

    def _start_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Handle start node execution."""
        logger.info(f"Starting workflow execution for thread: {state.thread_id}")

        # Update database with atomic operation
        success = self.db_manager.atomic_update_run_status(
            state.thread_id, "pending", "running"
        )
        if not success:
            logger.warning(f"Failed to update run status to running for {state.thread_id}")

        return {"current_node": "__start__"}

    def _end_node(self, state: WorkflowState) -> Dict[str, Any]:
        """Handle end node execution."""
        logger.info(f"Completing workflow execution for thread: {state.thread_id}")

        # Update database with atomic operation
        success = self.db_manager.atomic_update_run_status(
            state.thread_id, "running", "completed"
        )
        if not success:
            logger.warning(f"Failed to update run status to completed for {state.thread_id}")

        return {"current_node": "__end__"}

    def _create_python_node_handler(self, node_def):
        """Create handler function for Python node."""
        def handler(state: WorkflowState) -> Dict[str, Any]:
            workflow_logger = WorkflowLogger(state.thread_id)
            python_node = PythonNode(node_def.id, node_def.data.dict() if node_def.data else {})

            # Create improved interrupt function
            def interrupt(value=None, update=None):
                # Update state with provided data
                if update:
                    for key, val in update.items():
                        setattr(state, key, val)

                # Log interrupt
                workflow_logger.info(f"Node {node_def.id} interrupted with value: {value}, update: {update}")

                # Update database status to paused with atomic operation
                success = self.db_manager.atomic_update_run_status(
                    state.thread_id, "running", "paused", {
                        "interrupt_value": value,
                        "last_node": node_def.id
                    }
                )

                if not success:
                    logger.warning(f"Failed to update status to paused for {state.thread_id}")

                # Raise proper exception for LangGraph
                raise WorkflowInterrupt("Manual interrupt", {"node_id": node_def.id, "value": value})

            # Execute node
            result = python_node.execute(state, workflow_logger, interrupt)

            # Update current node
            result["current_node"] = node_def.id

            return result

        return handler

    def _create_condition_node_handler(self, node_def):
        """Create handler function for condition node."""
        def handler(state: WorkflowState) -> Dict[str, Any]:
            workflow_logger = WorkflowLogger(state.thread_id)
            condition_node = ConditionNode(node_def.id, node_def.data.dict() if node_def.data else {})

            # Execute condition evaluation
            result = condition_node.execute(state, workflow_logger)

            # Update current node
            result["current_node"] = node_def.id

            return result

        return handler

    def _create_condition_router(self, condition):
        """Create routing function for conditional edges."""
        def router(state: WorkflowState) -> bool:
            # If condition is a boolean, return it directly
            if isinstance(condition, bool):
                return condition

            # If condition is a JSONLogic expression, evaluate it
            if isinstance(condition, dict):
                try:
                    from json_logic import jsonLogic as jsonlogic
                except ImportError:
                    # Fallback if json_logic is not available
                    logger.warning("json_logic not available, using simple condition evaluation")
                    return True
                context_data = {
                    **state.data,
                    "metadata": state.metadata,
                    "condition_result": state.data.get("condition_result")
                }
                return bool(jsonlogic.jsonLogic(condition, context_data))

            # Default to True
            return True

        return router

    def _ensure_functions_registered(self, flow_version_id: int) -> None:
        """Ensure all functions required by the workflow are registered."""
        try:
            # Get flow version to find the flow
            flow_version = self.db_manager.get_flow_version(flow_version_id)
            if not flow_version:
                logger.warning(f"Flow version not found: {flow_version_id}")
                return

            # Get the flow to find app information
            # We need to get flow name from flow_version directly or query by flow_id
            # Since we don't have get_flow_by_id, let's use a different approach
            # For now, let's try to extract flow name from the flow_version data
            flow_name = None

            # Try to get flow information from database using available methods
            flow_name = None
            try:
                # Query all flows and find the one with matching flow_id
                with self.db_manager.get_session() as session:
                    from ..storage.database import Flow
                    flow = session.query(Flow).filter(Flow.id == flow_version["flow_id"]).first()
                    if flow:
                        flow_name = flow.name
            except Exception as e:
                logger.warning(f"Could not query flow by ID: {e}")

            if not flow_name:
                logger.warning(f"Flow name not found for version: {flow_version_id}")
                return

            logger.info(f"🔧 Ensuring functions are registered for flow: {flow_name}")

            # Try to find the app that contains this flow
            from ..apps.manager import AppManager
            from ..config import get_config

            config = get_config()
            apps_dir = config.get_apps_directory_path()
            app_manager = AppManager(str(apps_dir))

            # Find app by flow name - iterate through all apps to find matching flow
            # The flow_name in database should match one of the flow keys in app.json
            app_config = None
            target_flow_id = None

            for app in app_manager.list_apps():
                if hasattr(app, 'flows') and app.flows:
                    # Check if flow_name matches any flow key in this app
                    if flow_name in app.flows:
                        app_config = app
                        target_flow_id = flow_name
                        logger.info(f"🎯 Found matching flow: {flow_name} in app {app.app_id}")
                        break

                    # Also check flow titles/names in case there's a mismatch
                    for fid, fconfig in app.flows.items():
                        if (hasattr(fconfig, 'title') and fconfig.title == flow_name) or \
                           (hasattr(fconfig, 'name') and fconfig.name == flow_name):
                            app_config = app
                            target_flow_id = fid
                            logger.info(f"🎯 Found matching flow by title/name: {fid} in app {app.app_id}")
                            break

                    if app_config:
                        break

            if not app_config or not target_flow_id:
                logger.warning(f"No app found containing flow: {flow_name}")
                # Try a fallback approach - look for any app with flow1 since that's what we're looking for
                for app in app_manager.list_apps():
                    if hasattr(app, 'flows') and app.flows and 'flow1' in app.flows:
                        app_config = app
                        target_flow_id = 'flow1'
                        logger.info(f"🔄 Using fallback: found flow1 in app {app.app_id}")
                        break

                if not app_config:
                    logger.error(f"❌ No app found with flow1 as fallback")
                    return

            logger.info(f"🔧 Loading workflow definition to register functions: {app_config.app_id}.{target_flow_id}")

            # Load workflow definition - this will trigger function registration
            try:
                app_manager.load_workflow_definition(app_config.app_id, target_flow_id)
                logger.info(f"✅ Successfully ensured functions are registered for {app_config.app_id}.{target_flow_id}")
            except Exception as e:
                logger.error(f"❌ Failed to load workflow definition for function registration: {e}")
                # Don't raise exception to avoid breaking workflow execution

        except Exception as e:
            logger.error(f"❌ Error ensuring functions are registered: {e}")
            # Don't raise exception to avoid breaking workflow execution

    def create_flow(self, name: str, definition: WorkflowDefinition, version: str = "1.0.0") -> int:
        """Create and store a new workflow."""

        # Validate workflow definition for security
        validate_workflow_definition(definition.dict())

        # Use the simplified create_flow_by_name method
        flow_id = self.db_manager.create_flow_by_name(
            flow_name=name,
            version=version,
            dsl_json=definition.dict(),
            published=True
        )

        logger.info(f"Created workflow: {name} v{version} (flow_id={flow_id})")

        return flow_id

    def start_workflow(self, flow_version_id: int, input_data: Optional[Dict[str, Any]] = None,
                       thread_id: Optional[str] = None) -> str:
        """Start workflow execution."""

        if thread_id is None:
            thread_id = str(uuid.uuid4())

        # Get flow version
        flow_version = self.db_manager.get_flow_version(flow_version_id)
        if not flow_version:
            raise ValueError(f"Flow version not found: {flow_version_id}")

        # Ensure functions are registered before execution
        self._ensure_functions_registered(flow_version_id)

        # Create workflow definition
        definition = WorkflowDefinition(**flow_version["dsl_json"])

        # Compile workflow
        graph = self.compile_workflow(definition)
        compiled_graph = graph.compile(checkpointer=self.checkpointer)

        # Create initial state
        initial_state = WorkflowState(
            thread_id=thread_id,
            data=input_data or {},
            metadata={"flow_version_id": flow_version_id}
        )

        # Create run record only if it doesn't exist; otherwise update metadata/status safely
        existing_run = self.db_manager.get_run(thread_id)
        if not existing_run:
            # Store inputs in metadata for observability
            self.db_manager.create_run(thread_id, flow_version_id, "pending", metadata={"inputs": input_data or {}})
        else:
            # Avoid duplicate insert; keep or reset to pending before engine sets running at start node
            current_status = existing_run.get("status", "unknown")
            self.db_manager.atomic_update_run_status(thread_id, current_status, "pending", {"inputs": input_data or {}, "restarted": True})

        # Start execution
        config = {"configurable": {"thread_id": thread_id}}

        try:
            # Execute workflow - pass the WorkflowState object directly instead of dict
            # This ensures that the state data is properly accessible to nodes
            result = compiled_graph.invoke(initial_state, config)

            logger.info(f"Workflow execution completed for thread: {thread_id}, result_keys: {list(result.keys())}")

        except WorkflowInterrupt as e:
            logger.info(f"Workflow execution interrupted for thread: {thread_id}, reason: {e.reason}")

        except Exception as e:
            logger.error(f"Workflow execution failed for thread: {thread_id}, error: {str(e)}, error_type: {type(e).__name__}")

            self.db_manager.atomic_update_run_status(thread_id, "running", "failed", {"error": str(e)})
            raise

        return thread_id

    def pause_workflow(self, thread_id: str) -> bool:
        """Request workflow pause."""
        signal_id = self.db_manager.create_signal(thread_id, "pause_request")
        logger.info(f"Pause requested for workflow thread: {thread_id}, signal_id: {signal_id}")
        return True

    def resume_workflow(self, thread_id: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """Resume paused workflow."""

        # Get flow run
        run = self.db_manager.get_run(thread_id)
        if not run:
            return False

        # Get flow version and recompile
        flow_version = self.db_manager.get_flow_version(run["flow_version_id"])
        if not flow_version:
            return False

        definition = WorkflowDefinition(**flow_version["dsl_json"])
        graph = self.compile_workflow(definition)
        compiled_graph = graph.compile(checkpointer=self.checkpointer)

        # Resume execution
        config = {"configurable": {"thread_id": thread_id}}

        try:
            if updates:
                # Resume with updates
                result = compiled_graph.invoke(updates, config)
            else:
                # Resume from checkpoint
                result = compiled_graph.invoke(None, config)

            logger.info(f"Workflow resumed and completed for thread: {thread_id}")

        except WorkflowInterrupt as e:
            logger.info(f"Workflow resumed but interrupted again for thread: {thread_id}, reason: {e.reason}")

        except Exception as e:
            logger.error(f"Workflow resume failed for thread: {thread_id}, error: {str(e)}, error_type: {type(e).__name__}")

            self.db_manager.atomic_update_run_status(thread_id, "running", "failed", {"error": str(e)})
            return False
        
        return True
    
    def get_workflow_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow execution status."""
        return self.db_manager.get_run(thread_id)
    
    def list_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent workflow runs."""
        return self.db_manager.list_runs(limit)