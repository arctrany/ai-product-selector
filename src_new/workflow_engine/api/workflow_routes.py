"""Deprecated workflow execution API routes.

This module contains deprecated API routes that are kept for backward compatibility.
New applications should use the thread control APIs in thread_routes.py instead.

Deprecated routes:
- All /api/runs/* endpoints are deprecated
- Use /api/thread/{thread_id}/* endpoints instead
"""

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
    """Create deprecated workflow execution routes for backward compatibility."""
    router = APIRouter(prefix="/runs", tags=["workflows-deprecated"])

    @router.delete("/{thread_id}")
    async def cancel_workflow(
        thread_id: str,
        control: WorkflowControl = Depends(workflow_control_dependency)
    ):
        """Cancel workflow execution.

        DEPRECATED: This endpoint is deprecated. Use DELETE /api/thread/{thread_id} instead.
        """
        try:
            success = control.cancel_workflow(thread_id, "Cancelled via deprecated API")
            if not success:
                raise WorkflowNotFoundException(thread_id)

            logger.warning(f"Using deprecated cancel API for workflow: {thread_id}")
            return {"thread_id": thread_id, "status": "cancelled", "deprecated": True}
        
        except WorkflowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to cancel workflow: {e}")
            raise ValidationException(f"Failed to cancel workflow: {str(e)}")

    return router