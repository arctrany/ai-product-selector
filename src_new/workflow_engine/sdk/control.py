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

            logger.info(f"Pause requested for workflow {thread_id}",
                        context={"signal_id": signal_id, "node_id": node_id})

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

            logger.info(f"Resume requested for workflow {thread_id}",
                        context={"signal_id": signal_id, "has_updates": bool(updates)})

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

            logger.info(f"Cancel requested for workflow {thread_id}",
                        context={"signal_id": signal_id, "reason": reason})

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
            # This delegates to the engine using the same database path
            # Get the database path from the current db_manager
            from ..core.engine import WorkflowEngine
            db_path = self.db_manager.db_path if hasattr(self.db_manager, 'db_path') else None
            engine = WorkflowEngine(db_path)
            return engine.start_workflow(flow_version_id, input_data, thread_id)
        except Exception as e:
            logger.error(f"Failed to start workflow: {str(e)}")
            raise
