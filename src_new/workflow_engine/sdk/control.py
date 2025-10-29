"""Workflow control utilities for fine-grained execution management."""

import time
from typing import Any, Dict, Optional, List
from ..storage.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class WorkflowControl:
    """Provides fine-grained control over workflow execution."""

    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db_manager = db_manager or DatabaseManager()

    def pause_workflow(self, thread_id: str, node_id: Optional[str] = None) -> bool:
        """Request workflow pause at current or specific node.

        Args:
            thread_id: Workflow thread identifier
            node_id: Optional specific node to pause at

        Returns:
            True if pause request was successful
        """
        try:
            # Create pause signal
            signal_data = {"node_id": node_id} if node_id else {}
            signal_id = self.db_manager.create_signal(thread_id, "pause_request", signal_data)

            logger.info(f"Pause requested for workflow {thread_id}, signal_id: {signal_id}, node_id: {node_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to pause workflow {thread_id}: {str(e)}")
            return False

    def resume_workflow(self, thread_id: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """Resume paused workflow execution.

        Args:
            thread_id: Workflow thread identifier
            updates: Optional state updates to apply on resume

        Returns:
            True if resume request was successful
        """
        try:
            # Create resume signal
            signal_data = {"updates": updates} if updates else {}
            signal_id = self.db_manager.create_signal(thread_id, "resume_request", signal_data)

            logger.info(f"Resume requested for workflow {thread_id}, signal_id: {signal_id}, has_updates: {bool(updates)}")

            return True

        except Exception as e:
            logger.error(f"Failed to resume workflow {thread_id}: {str(e)}")
            return False

    def cancel_workflow(self, thread_id: str, reason: Optional[str] = None) -> bool:
        """Cancel workflow execution.

        Args:
            thread_id: Workflow thread identifier
            reason: Optional cancellation reason

        Returns:
            True if cancellation request was successful
        """
        try:
            # Create cancel signal
            signal_data = {"reason": reason} if reason else {}
            signal_id = self.db_manager.create_signal(thread_id, "cancel_request", signal_data)

            logger.info(f"Cancel requested for workflow {thread_id}, signal_id: {signal_id}, reason: {reason}")

            return True

        except Exception as e:
            logger.error(f"Failed to cancel workflow {thread_id}: {str(e)}")
            return False

    def get_workflow_status(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status and state.

        Args:
            thread_id: Workflow thread identifier

        Returns:
            Workflow status information or None if not found
        """
        try:
            return self.db_manager.get_run(thread_id)
        except Exception as e:
            logger.error(f"Failed to get workflow status for {thread_id}: {str(e)}")
            return None

    def list_workflows(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List recent workflow runs.

        Args:
            limit: Maximum number of runs to return

        Returns:
            List of workflow run information
        """
        try:
            runs = self.db_manager.list_runs(limit=limit)
            return [run for run in runs] if runs else []
        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            return []

    def get_workflow_logs(self, thread_id: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get workflow execution logs.

        Args:
            thread_id: Workflow thread identifier
            limit: Maximum number of log entries to return

        Returns:
            List of log entries
        """
        try:
            # This would typically read from log files or database
            # For now, return empty list as logs are handled separately
            return []
        except Exception as e:
            logger.error(f"Failed to get logs for {thread_id}: {str(e)}")
            return []

    def wait_for_completion(self, thread_id: str, timeout_seconds: Optional[float] = None) -> bool:
        """Wait for workflow to complete.

        Args:
            thread_id: Workflow thread identifier
            timeout_seconds: Optional timeout in seconds

        Returns:
            True if workflow completed, False if timeout or error
        """
        start_time = time.time()

        while True:
            status = self.get_workflow_status(thread_id)
            if not status:
                return False

            if status["status"] in ["completed", "failed", "cancelled"]:
                return status["status"] == "completed"

            # Check timeout
            if timeout_seconds and (time.time() - start_time) > timeout_seconds:
                logger.warning(f"Timeout waiting for workflow {thread_id} completion")
                return False

            time.sleep(0.1)  # Poll every 100ms

    def get_active_signals(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get active control signals for a workflow.

        Args:
            thread_id: Workflow thread identifier

        Returns:
            List of active signals
        """
        try:
            # This would need to be implemented in DatabaseManager
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get signals for {thread_id}: {str(e)}")
            return []

    def start_workflow(self, flow_version_id: int, input_data: Optional[Dict[str, Any]] = None,
                       thread_id: Optional[str] = None) -> str:
        """Start workflow execution.

        Args:
            flow_version_id: Flow version ID to execute
            input_data: Optional input data for the workflow
            thread_id: Optional custom thread ID

        Returns:
            Thread ID of the started workflow
        """
        try:
            # This delegates to the engine using the same database configuration
            from ..core.engine import WorkflowEngine
            from ..core.config import WorkflowEngineConfig

            # Create a config with the same database path if available
            if hasattr(self.db_manager, 'db_path') and self.db_manager.db_path:
                config = WorkflowEngineConfig()
                config.db_path = self.db_manager.db_path
                engine = WorkflowEngine(config)
            else:
                # Use default config
                engine = WorkflowEngine()

            return engine.start_workflow(flow_version_id, input_data, thread_id)
        except Exception as e:
            logger.error(f"Failed to start workflow: {str(e)}")
            raise

    async def start_workflow_async(self, flow_version_id: int, input_data: Optional[Dict[str, Any]] = None,
                                   thread_id: Optional[str] = None) -> str:
        """Start workflow execution asynchronously.

        Args:
            flow_version_id: Flow version ID to execute
            input_data: Optional input data for the workflow
            thread_id: Optional custom thread ID

        Returns:
            Thread ID of the started workflow
        """
        import asyncio
        import threading
        import uuid

        try:
            # Generate thread_id if not provided, with enhanced uniqueness
            if thread_id is None:
                timestamp = int(time.time() * 1000000)  # Microsecond timestamp
                random_part = uuid.uuid4().hex[:8]
                thread_id = f"thr_{timestamp}_{random_part}"
                logger.info(f"🆕 Generated new async workflow instance: thread_id={thread_id}, flow_version_id={flow_version_id}, timestamp={timestamp}")
            else:
                logger.info(f"🔄 Reusing provided thread_id for async workflow: {thread_id}, flow_version_id={flow_version_id}")

            # Check if run already exists and handle accordingly
            existing_run = None
            try:
                existing_run = self.db_manager.get_run(thread_id)
            except Exception:
                # Run doesn't exist, which is fine
                pass

            if existing_run:
                # Run already exists, check its status
                if existing_run["status"] in ["running", "completed", "failed", "cancelled"]:
                    # Cannot start already processed run
                    raise ValueError(f"Workflow {thread_id} is already {existing_run['status']}")
                elif existing_run["status"] == "pending":
                    # Run exists and is pending, we can proceed to start it
                    logger.info(f"Found existing pending run with thread_id: {thread_id}, starting execution")
                else:
                    # Unknown status, create new thread_id to avoid conflicts
                    logger.warning(f"Run {thread_id} has unknown status {existing_run['status']}, generating new thread_id")
                    timestamp = int(time.time() * 1000000)
                    random_part = uuid.uuid4().hex[:8]
                    thread_id = f"thr_{timestamp}_{random_part}"
                    existing_run = None

            # Create run record if it doesn't exist, with retry mechanism for conflicts
            if not existing_run:
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        self.db_manager.create_run(thread_id, flow_version_id, "pending", metadata={"inputs": input_data or {}})
                        logger.info(f"Created async workflow run with thread_id: {thread_id}")
                        break
                    except Exception as e:
                        if "UNIQUE constraint failed" in str(e) and attempt < max_retries - 1:
                            # Generate new thread_id and retry
                            logger.warning(f"Thread ID {thread_id} already exists, generating new one (attempt {attempt + 1})")
                            timestamp = int(time.time() * 1000000)
                            random_part = uuid.uuid4().hex[:8]
                            thread_id = f"thr_{timestamp}_{random_part}"
                            continue
                        else:
                            # Final attempt failed or different error
                            raise

            # Start workflow execution in background thread
            def run_workflow():
                try:
                    from ..core.engine import WorkflowEngine
                    from ..core.config import WorkflowEngineConfig

                    # Create a config with the same database path if available
                    if hasattr(self.db_manager, 'db_path') and self.db_manager.db_path:
                        config = WorkflowEngineConfig()
                        config.db_path = self.db_manager.db_path
                        engine = WorkflowEngine(config)
                    else:
                        # Use default config
                        engine = WorkflowEngine()

                    # Execute workflow - this will update the status from pending to running
                    engine.start_workflow(flow_version_id, input_data, thread_id)

                except Exception as e:
                    logger.error(f"Async workflow execution failed for thread {thread_id}: {str(e)}")
                    # Update status to failed
                    try:
                        self.db_manager.atomic_update_run_status(thread_id, "running", "failed", {"error": str(e)})
                    except Exception as update_e:
                        logger.error(f"Failed to update run status to failed: {update_e}")

            # Start background thread
            workflow_thread = threading.Thread(target=run_workflow, daemon=True)
            workflow_thread.start()

            logger.info(f"Started async workflow execution for thread_id: {thread_id}")
            return thread_id

        except Exception as e:
            logger.error(f"Failed to start async workflow: {str(e)}")
            # Clean up the run record if it was created
            try:
                if thread_id:
                    self.db_manager.atomic_update_run_status(thread_id, "pending", "failed", {"error": str(e)})
            except Exception:
                pass
            raise
