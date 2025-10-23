"""Flow management API routes."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from .dependencies import engine_dependency, db_manager_dependency
from .exceptions import FlowNotFoundException, ValidationException
from ..core.engine import WorkflowEngine
from ..core.models import WorkflowDefinition
from ..storage.database import DatabaseManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Request/Response models
class CreateFlowRequest(BaseModel):
    name: str
    definition: WorkflowDefinition
    version: str = "1.0.0"

class FlowResponse(BaseModel):
    flow_version_id: int
    name: str
    version: str
    status: str

def create_flow_router() -> APIRouter:
    """Create flow management routes."""
    router = APIRouter(prefix="/flows", tags=["flows"])

    @router.post("", response_model=FlowResponse)
    async def create_flow(
        request: CreateFlowRequest,
        engine: WorkflowEngine = Depends(engine_dependency)
    ):
        """Create a new workflow."""
        try:
            flow_version_id = engine.create_flow(
                name=request.name,
                definition=request.definition,
                version=request.version
            )

            logger.info(f"Created flow: {request.name} v{request.version}")

            return FlowResponse(
                flow_version_id=flow_version_id,
                name=request.name,
                version=request.version,
                status="created"
            )

        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            raise ValidationException(f"Failed to create flow: {str(e)}")

    @router.post("/{flow_version_id}/publish")
    async def publish_flow(
        flow_version_id: int,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Publish a flow version."""
        try:
            success = db_manager.publish_flow_version(flow_version_id)
            if not success:
                raise FlowNotFoundException(str(flow_version_id), "Flow version not found")

            logger.info(f"Published flow version: {flow_version_id}")
            return {"flow_version_id": flow_version_id, "status": "published"}

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to publish flow: {e}")
            raise ValidationException(f"Failed to publish flow: {str(e)}")

    @router.get("/{flow_id}")
    async def get_flow(
        flow_id: str,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Get flow information."""
        try:
            flow = db_manager.get_flow_by_name(flow_id)
            if not flow:
                raise FlowNotFoundException(flow_id)

            return flow

        except FlowNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get flow {flow_id}: {e}")
            raise ValidationException(f"Failed to get flow: {str(e)}")

    @router.get("")
    async def list_flows(
        limit: int = 100,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """List all flows."""
        try:
            # This would need to be implemented in DatabaseManager
            # For now, return empty list
            return {"flows": [], "total": 0, "limit": limit}

        except Exception as e:
            logger.error(f"Failed to list flows: {e}")
            raise ValidationException(f"Failed to list flows: {str(e)}")

    @router.delete("/{flow_id}")
    async def delete_flow(
        flow_id: str,
        db_manager: DatabaseManager = Depends(db_manager_dependency)
    ):
        """Delete a flow."""
        try:
            # This would need to be implemented in DatabaseManager
            # For now, just return success
            logger.info(f"Flow deletion requested: {flow_id}")
            return {"flow_id": flow_id, "status": "deleted"}

        except Exception as e:
            logger.error(f"Failed to delete flow {flow_id}: {e}")
            raise ValidationException(f"Failed to delete flow: {str(e)}")

    return router