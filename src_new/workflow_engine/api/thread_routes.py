"""Thread control API routes for workflow execution management."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from pydantic import BaseModel

from .dependencies import workflow_control_dependency, db_manager_dependency, config_dependency
from .exceptions import WorkflowNotFoundException, ValidationException
from ..sdk.control import WorkflowControl
from ..storage.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Request/Response models
class ThreadControlRequest(BaseModel):
    updates: Optional[Dict[str, Any]] = None

class ThreadStatusResponse(BaseModel):
    thread_id: str
    status: str
    flow_version_id: Optional[int] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    last_event_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ThreadControlResponse(BaseModel):
    thread_id: str
    status: str
    message: str

class ThreadLogsResponse(BaseModel):
    thread_id: str
    logs: list
    total: int

def create_thread_router() -> APIRouter:
    """Create thread control routes."""
    router = APIRouter(prefix="/thread", tags=["threads"])

    def validate_thread_exists(thread_id: str, db_manager: DatabaseManager) -> Dict[str, Any]:
        """Validate that thread exists and return thread info."""
        thread_info = db_manager.get_run(thread_id)
        if not thread_info:
            raise WorkflowNotFoundException(thread_id, "Thread not found")
        return thread_info

    @router.post("/{thread_id}/start", response_model=ThreadControlResponse)
    async def start_thread(
        thread_id: str = Path(..., description="Thread ID to start"),
        request: ThreadControlRequest = ThreadControlRequest(),
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Start a thread execution.
        
        Note: This endpoint is for starting a thread that was created but not yet started.
        For creating and starting a new workflow, use /api/flows/{flow_id}/start/latest instead.
        """
        try:
            # Validate thread exists and is in a startable state
            thread_info = validate_thread_exists(thread_id, db_manager)
            
            current_status = thread_info.get("status", "unknown")
            if current_status not in ["pending", "paused"]:
                raise ValidationException(f"Thread {thread_id} cannot be started from status: {current_status}")

            # Get flow version info for starting
            flow_version_id = thread_info.get("flow_version_id")
            if not flow_version_id:
                raise ValidationException(f"Thread {thread_id} has no associated flow version")

            # Start the workflow using the control
            started_thread_id = control.start_workflow(
                flow_version_id=flow_version_id,
                input_data=thread_info.get("metadata", {}).get("inputs", {}),
                thread_id=thread_id
            )

            logger.info(f"Started thread: {thread_id}")

            return ThreadControlResponse(
                thread_id=started_thread_id,
                status="started",
                message=f"Thread {thread_id} started successfully"
            )

        except WorkflowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to start thread {thread_id}: {e}")
            raise ValidationException(f"Failed to start thread: {str(e)}")

    @router.post("/{thread_id}/pause", response_model=ThreadControlResponse)
    async def pause_thread(
        thread_id: str = Path(..., description="Thread ID to pause"),
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Pause thread execution."""
        try:
            # Validate thread exists
            validate_thread_exists(thread_id, db_manager)
            
            success = control.pause_workflow(thread_id)
            if not success:
                raise ValidationException(f"Failed to pause thread {thread_id}")

            logger.info(f"Paused thread: {thread_id}")

            return ThreadControlResponse(
                thread_id=thread_id,
                status="pause_requested",
                message="Pause request sent"
            )

        except WorkflowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to pause thread {thread_id}: {e}")
            raise ValidationException(f"Failed to pause thread: {str(e)}")

    @router.post("/{thread_id}/resume", response_model=ThreadControlResponse)
    async def resume_thread(
        thread_id: str = Path(..., description="Thread ID to resume"),
        request: ThreadControlRequest = ThreadControlRequest(),
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Resume paused thread."""
        try:
            # Validate thread exists
            validate_thread_exists(thread_id, db_manager)
            
            success = control.resume_workflow(thread_id, request.updates)
            if not success:
                raise ValidationException(f"Failed to resume thread {thread_id}")

            logger.info(f"Resumed thread: {thread_id}")

            return ThreadControlResponse(
                thread_id=thread_id,
                status="resumed",
                message="Thread resumed"
            )

        except WorkflowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to resume thread {thread_id}: {e}")
            raise ValidationException(f"Failed to resume thread: {str(e)}")

    @router.post("/{thread_id}/stop", response_model=ThreadControlResponse)
    async def stop_thread(
        thread_id: str = Path(..., description="Thread ID to stop"),
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Stop (cancel) thread execution permanently."""
        try:
            # Validate thread exists
            validate_thread_exists(thread_id, db_manager)

            success = control.cancel_workflow(thread_id, "User requested stop")
            if not success:
                raise ValidationException(f"Failed to stop thread {thread_id}")

            logger.info(f"Stopped thread: {thread_id}")

            return ThreadControlResponse(
                thread_id=thread_id,
                status="stopped",
                message="Thread stopped successfully"
            )

        except WorkflowNotFoundException:
            raise
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to stop thread {thread_id}: {e}")
            raise ValidationException(f"Failed to stop thread: {str(e)}")

    @router.get("/{thread_id}/status", response_model=ThreadStatusResponse)
    async def get_thread_status(
        thread_id: str = Path(..., description="Thread ID to get status for"),
        control: WorkflowControl = Depends(workflow_control_dependency),
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Get thread execution status."""
        try:
            # Validate thread exists and get status
            thread_info = validate_thread_exists(thread_id, db_manager)
            
            return ThreadStatusResponse(
                thread_id=thread_id,
                status=thread_info.get("status", "unknown"),
                flow_version_id=thread_info.get("flow_version_id"),
                started_at=thread_info.get("started_at"),
                finished_at=thread_info.get("finished_at"),
                last_event_at=thread_info.get("last_event_at"),
                metadata=thread_info.get("metadata", {})
            )

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get thread status for {thread_id}: {e}")
            raise ValidationException(f"Failed to get thread status: {str(e)}")

    @router.get("/{thread_id}/logs", response_model=ThreadLogsResponse)
    async def get_thread_logs(
        thread_id: str = Path(..., description="Thread ID to get logs for"),
        limit: int = 1000,
        db_manager: DatabaseManager = Depends(db_manager_dependency),
        config=Depends(config_dependency)
    ):
        """Get thread execution logs."""
        try:
            # Validate thread exists
            validate_thread_exists(thread_id, db_manager)
            
            # Try to get logs from file system using configuration
            try:
                import json
                from pathlib import Path

                # Get log directory path from configuration
                log_dir_path = config.get_logging_directory_path()
                log_dir = log_dir_path / "runs" / thread_id
                log_file = log_dir / "logs.jsonl"

                logs = []
                if log_file.exists():
                    with open(log_file, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        # Get last N lines
                        for line in lines[-limit:]:
                            if line.strip():
                                logs.append(json.loads(line.strip()))

                return ThreadLogsResponse(
                    thread_id=thread_id,
                    logs=logs,
                    total=len(logs)
                )

            except Exception as log_error:
                logger.warning(f"Failed to read log file for {thread_id}: {log_error}")
                # Return empty logs if file reading fails
                return ThreadLogsResponse(
                    thread_id=thread_id,
                    logs=[],
                    total=0
                )

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get logs for {thread_id}: {e}")
            raise ValidationException(f"Failed to get logs: {str(e)}")

    return router