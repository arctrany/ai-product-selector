"""Workflow execution API routes."""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .dependencies import engine_dependency, config_dependency, workflow_control_dependency
from .exceptions import WorkflowNotFoundException, ValidationException
from ..core.engine import WorkflowEngine
from ..sdk.control import WorkflowControl
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Request/Response models
class StartWorkflowRequest(BaseModel):
    flow_version_id: int
    input_data: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None

class ResumeWorkflowRequest(BaseModel):
    updates: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    thread_id: str
    status: str
    message: str

def create_workflow_router() -> APIRouter:
    """Create workflow execution routes."""
    router = APIRouter(prefix="/runs", tags=["workflows"])

    @router.post("/start", response_model=WorkflowResponse)
    async def start_workflow(
        request: StartWorkflowRequest,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Start workflow execution."""
        try:
            thread_id = control.start_workflow(
                flow_version_id=request.flow_version_id,
                input_data=request.input_data,
                thread_id=request.thread_id
            )

            logger.info(f"Started workflow: {thread_id}")

            return WorkflowResponse(
                thread_id=thread_id,
                status="started",
                message="Workflow execution started"
            )

        except Exception as e:
            logger.error(f"Failed to start workflow: {e}")
            raise ValidationException(f"Failed to start workflow: {str(e)}")

    @router.get("/{thread_id}")
    async def get_workflow_status(
        thread_id: str,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Get workflow execution status."""
        try:
            status = control.get_workflow_status(thread_id)
            if not status:
                raise WorkflowNotFoundException(thread_id)

            return status

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow status: {e}")
            raise ValidationException(f"Failed to get workflow status: {str(e)}")

    @router.post("/{thread_id}/pause", response_model=WorkflowResponse)
    async def pause_workflow(
        thread_id: str,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Pause workflow execution."""
        try:
            success = control.pause_workflow(thread_id)
            if not success:
                raise WorkflowNotFoundException(thread_id)

            logger.info(f"Paused workflow: {thread_id}")

            return WorkflowResponse(
                thread_id=thread_id,
                status="pause_requested",
                message="Pause request sent"
            )

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to pause workflow: {e}")
            raise ValidationException(f"Failed to pause workflow: {str(e)}")

    @router.post("/{thread_id}/resume", response_model=WorkflowResponse)
    async def resume_workflow(
        thread_id: str,
        request: ResumeWorkflowRequest,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Resume paused workflow."""
        try:
            success = control.resume_workflow(thread_id, request.updates)
            if not success:
                raise WorkflowNotFoundException(thread_id, "Workflow not found or cannot be resumed")

            logger.info(f"Resumed workflow: {thread_id}")

            return WorkflowResponse(
                thread_id=thread_id,
                status="resumed",
                message="Workflow resumed"
            )

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to resume workflow: {e}")
            raise ValidationException(f"Failed to resume workflow: {str(e)}")

    @router.get("")
    async def list_workflows(
        limit: int = 100,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """List recent workflow runs."""
        try:
            runs = control.list_workflows(limit)
            return {"runs": runs, "total": len(runs), "limit": limit}

        except Exception as e:
            logger.error(f"Failed to list workflows: {e}")
            raise ValidationException(f"Failed to list workflows: {str(e)}")

    @router.get("/{thread_id}/logs")
    async def get_workflow_logs(
        thread_id: str,
        limit: int = 1000,
        config=Depends(config_dependency)
    ):
        """Get workflow logs."""
        try:
            log_dir = config.get_logging_directory_path() / thread_id
            log_file = log_dir / "logs.jsonl"

            if not log_file.exists():
                return {"logs": [], "total": 0, "thread_id": thread_id}

            logs = []
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                # Get last N lines
                for line in lines[-limit:]:
                    if line.strip():
                        logs.append(json.loads(line.strip()))

            return {"logs": logs, "total": len(logs), "thread_id": thread_id}

        except Exception as e:
            logger.error(f"Failed to read logs for {thread_id}: {e}")
            raise ValidationException(f"Failed to read logs: {str(e)}")

    @router.get("/{thread_id}/logs/download")
    async def download_workflow_logs(
        thread_id: str,
        config=Depends(config_dependency)
    ):
        """Download workflow logs as file."""
        try:
            log_dir = config.get_logging_directory_path() / thread_id
            log_file = log_dir / "logs.jsonl"

            if not log_file.exists():
                raise WorkflowNotFoundException(thread_id, "Log file not found")

            return FileResponse(
                path=str(log_file),
                filename=f"workflow-{thread_id}-logs.jsonl",
                media_type="application/json"
            )

        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to download logs for {thread_id}: {e}")
            raise ValidationException(f"Failed to download logs: {str(e)}")

    @router.delete("/{thread_id}")
    async def cancel_workflow(
        thread_id: str,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Cancel workflow execution."""
        try:
            success = control.cancel_workflow(thread_id, "Cancelled via API")
            if not success:
                raise WorkflowNotFoundException(thread_id)
            
            logger.info(f"Cancelled workflow: {thread_id}")
            return {"thread_id": thread_id, "status": "cancelled"}
        
        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise ValidationException(f"Failed to cancel workflow: {str(e)}")

    return router